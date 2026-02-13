"""
Shared utilities for model loading, tokenizer setup, and common tasks.

Usage:
    from src.utils import load_model_and_tokenizer, print_gpu_stats
"""

import os
import logging
from typing import Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from src.config import ModelConfig, QLoRAConfig


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


def get_qlora_bnb_config(qlora_config: QLoRAConfig) -> BitsAndBytesConfig:
    """Build a BitsAndBytesConfig from a QLoRAConfig."""
    return BitsAndBytesConfig(
        load_in_4bit=qlora_config.load_in_4bit,
        bnb_4bit_quant_type=qlora_config.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=qlora_config.bnb_4bit_compute_dtype,
        bnb_4bit_use_double_quant=qlora_config.bnb_4bit_use_double_quant,
    )


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
    """Format messages using the tokenizer's chat template.
    
    Args:
        tokenizer: Loaded tokenizer with chat template
        messages: List of {"role": "...", "content": "..."} dicts
        add_generation_prompt: Whether to add the assistant prompt prefix
    
    Returns:
        Formatted prompt string
    """
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=add_generation_prompt,
    )
