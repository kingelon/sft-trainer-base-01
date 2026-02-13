"""
Shared utilities for model loading, tokenizer setup, dataset prep, and common tasks.

Usage:
    from src.utils import load_model_and_tokenizer, prepare_dataset, print_device_info
"""

import logging
import shutil
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from datasets import load_dataset, Dataset
from peft import PeftModel
from src.config import ModelConfig, QLoRAConfig, DataConfig, Recipe


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model & Tokenizer Loading
# ---------------------------------------------------------------------------

def load_tokenizer(model_config: ModelConfig) -> AutoTokenizer:
    """Load tokenizer for a model config."""
    logger.info(f"Loading tokenizer: {model_config.name}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_config.name,
        trust_remote_code=model_config.trust_remote_code,
    )
    # Ensure pad token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        logger.info(f"Set pad_token = eos_token ({tokenizer.eos_token})")
    return tokenizer


def load_model(
    model_config: ModelConfig,
    quantization_config: Optional[BitsAndBytesConfig] = None,
) -> AutoModelForCausalLM:
    """Load a causal LM, optionally with quantization."""
    logger.info(f"Loading model: {model_config.name} on {model_config.device}")

    kwargs = {
        "pretrained_model_name_or_path": model_config.name,
        "torch_dtype": model_config.dtype,
        "trust_remote_code": model_config.trust_remote_code,
    }

    if quantization_config:
        kwargs["quantization_config"] = quantization_config
        kwargs["device_map"] = "auto"
    else:
        kwargs["device_map"] = model_config.device

    model = AutoModelForCausalLM.from_pretrained(**kwargs)
    logger.info(f"Model loaded. Parameters: {model.num_parameters():,}")
    return model


def load_model_and_tokenizer(
    model_config: ModelConfig,
    quantization_config: Optional[BitsAndBytesConfig] = None,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Convenience: load both model and tokenizer."""
    tokenizer = load_tokenizer(model_config)
    model = load_model(model_config, quantization_config)
    return model, tokenizer


def load_model_with_lora(
    model_name: str,
    lora_path: str,
    device: Optional[str] = None,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load a base model and merge a LoRA adapter on top.

    Args:
        model_name: HF model ID or local path for the base model.
        lora_path: Path to the saved LoRA adapter directory.
        device: Target device (auto-detected if None).

    Returns:
        (model_with_lora, tokenizer)
    """
    from src.config import get_device, get_dtype

    if device is None:
        device = get_device()
    dtype = get_dtype(device)

    logger.info(f"Loading base model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=dtype, device_map=device,
    )

    logger.info(f"Loading LoRA adapter: {lora_path}")
    model = PeftModel.from_pretrained(model, lora_path)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def get_qlora_bnb_config(qlora_config: QLoRAConfig) -> BitsAndBytesConfig:
    """Build a BitsAndBytesConfig from a QLoRAConfig."""
    return BitsAndBytesConfig(
        load_in_4bit=qlora_config.load_in_4bit,
        bnb_4bit_quant_type=qlora_config.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=qlora_config.bnb_4bit_compute_dtype,
        bnb_4bit_use_double_quant=qlora_config.bnb_4bit_use_double_quant,
    )


def get_bnb_config_from_dict(quant_dict: dict) -> BitsAndBytesConfig:
    """Build BitsAndBytesConfig from a recipe quantization dict."""
    dtype_map = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    compute_dtype = dtype_map.get(
        quant_dict.get("bnb_4bit_compute_dtype", "bfloat16"),
        torch.bfloat16,
    )
    return BitsAndBytesConfig(
        load_in_4bit=quant_dict.get("load_in_4bit", True),
        bnb_4bit_quant_type=quant_dict.get("bnb_4bit_quant_type", "nf4"),
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=quant_dict.get("bnb_4bit_use_double_quant", True),
    )


# ---------------------------------------------------------------------------
# Dataset Preparation
# ---------------------------------------------------------------------------

def prepare_dataset(
    data_config: DataConfig,
    tokenizer: AutoTokenizer,
    data_path: Optional[str] = None,
) -> Dataset:
    """Load and prepare a dataset for training.

    Priority:
        1. data_path (CLI override) — loads from local file (jsonl/json/csv)
        2. data_config.default_dataset — loads from HF Hub

    The dataset is optionally truncated to max_samples and formatted
    using the tokenizer's chat template if text_field is None.

    Args:
        data_config: DataConfig from recipe.
        tokenizer: Loaded tokenizer for chat template formatting.
        data_path: Optional CLI override for data source.

    Returns:
        HF Dataset ready for SFTTrainer.
    """
    # --- Load raw dataset ---
    if data_path:
        path = Path(data_path)
        logger.info(f"Loading dataset from local file: {path}")
        if path.suffix == ".jsonl":
            dataset = load_dataset("json", data_files=str(path), split="train")
        elif path.suffix == ".json":
            dataset = load_dataset("json", data_files=str(path), split="train")
        elif path.suffix == ".csv":
            dataset = load_dataset("csv", data_files=str(path), split="train")
        else:
            raise ValueError(f"Unsupported data format: {path.suffix}")
    else:
        logger.info(f"Loading dataset from HF: {data_config.default_dataset}")
        dataset = load_dataset(data_config.default_dataset, split="train")

    # --- Truncate ---
    if data_config.max_samples and len(dataset) > data_config.max_samples:
        logger.info(f"Truncating to {data_config.max_samples} samples (from {len(dataset)})")
        dataset = dataset.select(range(data_config.max_samples))

    logger.info(f"Dataset ready: {len(dataset)} samples")
    logger.info(f"Columns: {dataset.column_names}")

    # --- Format with chat template if no text_field specified ---
    if data_config.text_field is None:
        fmt = data_config.format

        # Auto-detect format from dataset columns if not specified
        if fmt is None:
            if "context" in dataset.column_names and "answer" in dataset.column_names:
                fmt = "sql"
            elif "instruction" in dataset.column_names:
                fmt = "alpaca"

        if fmt == "sql":
            logger.info("Formatting dataset using chat template (SQL: context+question → SQL)")
            dataset = dataset.map(
                lambda ex: _format_sql_to_chat(ex, tokenizer),
                remove_columns=dataset.column_names,
            )
        else:
            logger.info("Formatting dataset using chat template (alpaca-style → chat messages)")
            dataset = dataset.map(
                lambda ex: _format_alpaca_to_chat(ex, tokenizer),
                remove_columns=dataset.column_names,
            )

    return dataset


def _format_alpaca_to_chat(example: dict, tokenizer: AutoTokenizer) -> dict:
    """Convert an alpaca-style example to chat template formatted text.

    Handles both examples with and without an 'input' field.
    """
    instruction = example.get("instruction", "")
    input_text = example.get("input", "")
    output_text = example.get("output", "")

    if input_text:
        user_content = f"{instruction}\n\n{input_text}"
    else:
        user_content = instruction

    messages = [
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": output_text},
    ]

    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False,
    )
    return {"text": formatted}


def _format_sql_to_chat(example: dict, tokenizer: AutoTokenizer) -> dict:
    """Convert a sql-create-context example to chat template formatted text.

    Expected fields: context (CREATE TABLE...), question, answer (SQL)
    """
    context = example.get("context", "")
    question = example.get("question", "")
    answer = example.get("answer", "")

    user_content = (
        f"Given the following SQL table schema:\n\n"
        f"{context}\n\n"
        f"Write a SQL query to answer: {question}"
    )

    messages = [
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": answer},
    ]

    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False,
    )
    return {"text": formatted}


# ---------------------------------------------------------------------------
# Output Directory Helpers
# ---------------------------------------------------------------------------

def create_output_dir(training_tag: str, base_dir: str = "./outputs/lora") -> Path:
    """Create a timestamped output directory for a training run.

    Returns:
        Path like outputs/lora/llama31-smoke_20260211_175400/
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = f"{training_tag}_{timestamp}"
    output_dir = Path(base_dir) / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    return output_dir


def save_recipe_copy(recipe_path: str, output_dir: Path):
    """Copy the recipe YAML into the output directory for reproducibility."""
    dest = output_dir / "recipe.yaml"
    shutil.copy2(recipe_path, dest)
    logger.info(f"Recipe saved to: {dest}")


# ---------------------------------------------------------------------------
# Device / Memory Helpers
# ---------------------------------------------------------------------------

def print_device_info():
    """Print available device information."""
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available:  {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device:     {torch.cuda.get_device_name(0)}")
        print(f"CUDA memory:     {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
    print(f"MPS available:   {torch.backends.mps.is_available()}")


def print_model_stats(model):
    """Print model parameter counts (total vs trainable)."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters:     {total:>12,}")
    print(f"Trainable parameters: {trainable:>12,}")
    print(f"Trainable %:          {100 * trainable / total:.4f}%")


# ---------------------------------------------------------------------------
# Chat Formatting Helpers
# ---------------------------------------------------------------------------

def format_chat_prompt(
    tokenizer: AutoTokenizer,
    messages: list[dict],
    add_generation_prompt: bool = True,
) -> str:
    """Format messages using the tokenizer's chat template."""
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=add_generation_prompt,
    )
