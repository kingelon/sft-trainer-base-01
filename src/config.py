"""
Central configuration for finetuning experiments.

Usage:
    from src.config import ModelConfig, LoRAConfig, TrainingConfig
    from src.config import load_recipe

All configs are dataclasses — modify defaults or instantiate with overrides.
Recipes are YAML files that produce these config objects via load_recipe().
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import torch
import yaml


def get_device() -> str:
    """Auto-detect best available device."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_dtype(device: str) -> torch.dtype:
    """Select appropriate dtype for device."""
    if device == "cuda":
        return torch.bfloat16
    elif device == "mps":
        return torch.float16
    return torch.float32


# ---------------------------------------------------------------------------
# Model Configs
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Configuration for a target model."""
    name: str = "meta-llama/Llama-3.1-8B-Instruct"
    device: str = field(default_factory=get_device)
    dtype: Optional[torch.dtype] = None
    trust_remote_code: bool = False
    max_seq_length: int = 2048

    def __post_init__(self):
        if self.dtype is None:
            self.dtype = get_dtype(self.device)


# Presets
LLAMA_31_8B = ModelConfig(name="meta-llama/Llama-3.1-8B-Instruct")
MISTRAL_7B_BASE = ModelConfig(name="mistralai/Mistral-7B-v0.1")
MISTRAL_7B_INSTRUCT = ModelConfig(name="mistralai/Mistral-7B-Instruct-v0.3")


# ---------------------------------------------------------------------------
# LoRA Configs
# ---------------------------------------------------------------------------

@dataclass
class LoRAConfig:
    """LoRA adapter configuration."""
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    bias: str = "none"
    task_type: str = "CAUSAL_LM"


@dataclass
class QLoRAConfig(LoRAConfig):
    """QLoRA config — adds quantization settings. Requires CUDA."""
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_compute_dtype: torch.dtype = torch.bfloat16
    bnb_4bit_use_double_quant: bool = True


# ---------------------------------------------------------------------------
# Training Configs
# ---------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    """Training hyperparameters."""
    output_dir: str = "./outputs/training"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.03
    weight_decay: float = 0.01
    logging_steps: int = 10
    save_strategy: str = "epoch"
    fp16: bool = False
    bf16: bool = True
    max_grad_norm: float = 0.3
    seed: int = 42


# ---------------------------------------------------------------------------
# Data Configs
# ---------------------------------------------------------------------------

@dataclass
class DataConfig:
    """Dataset configuration from recipe."""
    default_dataset: str = "yahma/alpaca-cleaned"
    text_field: Optional[str] = None
    max_samples: Optional[int] = None
    format: Optional[str] = None  # "sql", "alpaca", or None (auto-detect)


# ---------------------------------------------------------------------------
# Recipe Loader
# ---------------------------------------------------------------------------

@dataclass
class Recipe:
    """A complete training recipe parsed from YAML."""
    training_tag: str
    description: str
    model: ModelConfig
    lora: LoRAConfig
    training: TrainingConfig
    data: DataConfig
    quantization: Optional[Dict[str, Any]] = None
    raw: Optional[Dict[str, Any]] = None  # original YAML dict


def load_recipe(recipe_path: str) -> Recipe:
    """Load a YAML recipe file and return a Recipe object.

    Args:
        recipe_path: Path to the YAML recipe file.

    Returns:
        Recipe with all config objects populated.
    """
    path = Path(recipe_path)
    if not path.exists():
        raise FileNotFoundError(f"Recipe not found: {recipe_path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    # --- Model ---
    model_dict = raw.get("model", {})
    model_config = ModelConfig(
        name=model_dict.get("name", ModelConfig.name),
        max_seq_length=model_dict.get("max_seq_length", ModelConfig.max_seq_length),
        trust_remote_code=model_dict.get("trust_remote_code", False),
    )

    # --- LoRA ---
    lora_dict = raw.get("lora", {})
    lora_config = LoRAConfig(
        r=lora_dict.get("r", 16),
        lora_alpha=lora_dict.get("lora_alpha", 32),
        lora_dropout=lora_dict.get("lora_dropout", 0.05),
        target_modules=lora_dict.get("target_modules", ["q_proj", "v_proj"]),
        bias=lora_dict.get("bias", "none"),
        task_type=lora_dict.get("task_type", "CAUSAL_LM"),
    )

    # --- Training ---
    train_dict = raw.get("training", {})
    device = model_config.device

    # Auto-adjust fp16/bf16 based on device
    # NOTE: MPS does NOT support mixed-precision (AMP) training.
    # The model loads in float16 for memory, but training runs in float32.
    # Setting fp16=True on MPS causes gradient explosion → NaN → dead model.
    if device == "cuda":
        fp16, bf16 = False, True
    else:
        # MPS and CPU: train in float32
        fp16, bf16 = False, False

    training_config = TrainingConfig(
        num_train_epochs=train_dict.get("num_train_epochs", 3),
        per_device_train_batch_size=train_dict.get("per_device_train_batch_size", 4),
        gradient_accumulation_steps=train_dict.get("gradient_accumulation_steps", 4),
        learning_rate=train_dict.get("learning_rate", 2e-4),
        lr_scheduler_type=train_dict.get("lr_scheduler_type", "cosine"),
        warmup_ratio=train_dict.get("warmup_ratio", 0.03),
        weight_decay=train_dict.get("weight_decay", 0.01),
        logging_steps=train_dict.get("logging_steps", 10),
        save_strategy=train_dict.get("save_strategy", "epoch"),
        fp16=fp16,
        bf16=bf16,
        max_grad_norm=train_dict.get("max_grad_norm", 0.3),
        seed=train_dict.get("seed", 42),
    )

    # --- Data ---
    data_dict = raw.get("data", {})
    data_config = DataConfig(
        default_dataset=data_dict.get("default_dataset", "yahma/alpaca-cleaned"),
        text_field=data_dict.get("text_field"),
        max_samples=data_dict.get("max_samples"),
        format=data_dict.get("format"),
    )

    # --- Quantization ---
    quant_dict = raw.get("quantization")

    return Recipe(
        training_tag=raw.get("training_tag", "unnamed"),
        description=raw.get("description", ""),
        model=model_config,
        lora=lora_config,
        training=training_config,
        data=data_config,
        quantization=quant_dict,
        raw=raw,
    )
