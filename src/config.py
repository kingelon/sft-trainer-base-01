"""
Central configuration for finetuning experiments.

Usage:
    from src.config import ModelConfig, LoRAConfig, TrainingConfig

All configs are dataclasses — modify defaults or instantiate with overrides.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import torch


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
