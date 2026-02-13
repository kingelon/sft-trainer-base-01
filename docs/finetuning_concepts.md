# Finetuning Concepts Reference

Quick-reference for LoRA, QLoRA, and training concepts relevant to 7-8B scale models.

---

## LoRA (Low-Rank Adaptation)

- Freezes the base model weights
- Injects small trainable rank-decomposition matrices into attention layers
- Key params: `r` (rank), `lora_alpha` (scaling), `lora_dropout`, `target_modules`
- Typical targets: `q_proj`, `v_proj` (conservative) or all linear layers (aggressive)
- Adapter size: ~10-50MB depending on rank (vs 16GB+ for full model)

### Rank Selection Heuristic
| Rank | Use Case |
|------|----------|
| 4-8 | Style transfer, simple behavioral changes |
| 16-32 | Domain knowledge, format learning |
| 64-128 | Complex task adaptation |

---

## QLoRA (Quantized LoRA)

- Same as LoRA but base model is loaded in 4-bit (NF4 quantization)
- Requires `bitsandbytes` + CUDA GPU
- **Does NOT work on Mac MPS** — fallback to standard LoRA on Mac
- Reduces VRAM from ~16GB to ~6GB for 7B models
- Training quality is comparable to full-precision LoRA

### BitsAndBytes Config
```python
from transformers import BitsAndBytesConfig
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
```

---

## Training Considerations at 7-8B Scale

### What Works Well
- **Format/style transfer**: Teaching a model to respond in a specific format
- **Domain vocabulary**: Introducing specialized terminology
- **Tone adjustment**: Making responses more/less formal, concise, etc.
- **Simple task specialization**: Classification, extraction, summarization in a domain

### What's Harder
- **New factual knowledge**: Models struggle to reliably learn new facts via finetuning
- **Complex reasoning**: Can't easily add reasoning capabilities not present in base
- **Unlearning**: Difficult to make model forget specific behaviors

### Rules of Thumb
- Minimum ~100 high-quality examples for noticeable effect
- 500-1000 examples is a sweet spot for most adaptations
- Quality > quantity — 200 perfect examples beat 2000 noisy ones
- 1-3 epochs typically sufficient; more risks overfitting
- Learning rate: 1e-4 to 2e-5 range for LoRA

---

## Projecting to Larger Models

Key insight: techniques that work at 7-8B generally transfer to larger models with:
- Better baseline quality to build on
- Often need fewer examples for same effect
- Same LoRA rank can work (model capacity isn't the bottleneck)
- Training cost scales linearly with params

_Add observations and findings here as you experiment..._
