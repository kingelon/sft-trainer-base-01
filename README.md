# Finetuning Base

Experimentation scaffold for hands-on LLM finetuning — understanding model behaviors, input/output formats, and what's achievable at the 7-8B parameter scale.

## Target Models
- **Llama 3.1 8B Instruct** — Meta's instruction-tuned model
- **Mistral 7B** — Mistral AI's base/instruct model

## Techniques
- LoRA (Low-Rank Adaptation)
- QLoRA (Quantized LoRA)
- Hugging Face Transformers + PEFT + TRL

## Structure

```
├── agents/         # Agent context, ADR log, comms
├── docs/           # Reference documentation
├── notes/          # Freeform experiment notes
├── src/            # Shared config & utilities
├── scripts/        # Standalone experiment scripts
├── data/           # Datasets (symlinks + small files)
├── models/         # Model symlinks + finetuned adapters
├── outputs/        # Inference outputs, metrics
└── tests/          # Validation scripts
```

## Philosophy
1. **Standalone first** — each script is self-contained
2. **Small footprint** — no weights in repo, symlink to central HF cache
3. **Evolving** — grows into a framework as patterns stabilize
4. **Agent-aware** — `agents/` provides context for AI collaborators

## HF Cache
Using default HF cache at `~/.cache/huggingface`. Can be overridden later via `export HF_HOME=<path>` if centralization is needed.
