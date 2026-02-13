# ADR Log — Architecture Decision Records

Incremental log of decisions, actions, and observations. Append-only.

---

## ADR-001: Scaffold Creation
- **Date**: 2026-02-11
- **Context**: Setting up finetuning experimentation workspace from scratch. Vamsi wants standalone scripts, not a monolithic framework. Focus on Llama 3.1 8B and Mistral 7B.
- **Decision**: Created a directory-based scaffold with `agents/`, `docs/`, `notes/`, `src/`, `scripts/`, `data/`, `models/`, `outputs/`, `tests/`. Agent meta files in `agents/`. Shared config/utils in `src/`. Numbered script stubs in `scripts/`.
- **Consequences**: Easy to add new experiments as numbered scripts. `src/` can grow organically. No framework lock-in.

## ADR-002: HF Cache
- **Date**: 2026-02-11
- **Context**: Models are large (16-32GB). Multiple projects may need the same models.
- **Decision**: Using default HF cache (`~/.cache/huggingface`) for now. Can centralize later via `HF_HOME` env var if needed.
- **Consequences**: Simple setup, no env config required to get started. Revisit if disk usage becomes a concern across projects.

## ADR-003: Recipe-Driven Training Pipeline
- **Date**: 2026-02-11
- **Context**: Need a structured but flexible way to configure and run LoRA finetuning experiments. Want reproducibility and easy comparison of runs.
- **Decision**: YAML recipe files under `configs/training/` define model, LoRA, training, and data params. `scripts/train.py` takes `--recipe` and optional `--data` args. Outputs go to `outputs/lora/{tag}_{timestamp}/` with recipe copy, adapter, and metrics. `scripts/inference.py` supports `--compare` mode for base vs LoRA side-by-side.
- **Consequences**: Each run is self-documenting. Easy to create new recipes by copying YAML. MPS/CUDA auto-detection means same recipe works on different hardware.

## ADR-004: SQL Dataset for Demonstrating Finetuning Value
- **Date**: 2026-02-11
- **Context**: Need a dataset where finetuning produces a clearly visible, verifiable delta vs base model.
- **Decision**: Selected `b-mc2/sql-create-context` (78K examples). Base model generates generic SQL; finetuned model produces schema-aware queries with correct table/column names. Created `configs/training/llama31_sql_lora.yaml` (r=16, 1000 samples, 3 epochs) and test prompts under `data/sql_test_prompts.txt`.
- **Consequences**: Clear pass/fail evaluation (does SQL reference correct columns?). Real-world use case. 1000 samples is fast to train but enough to see impact.
