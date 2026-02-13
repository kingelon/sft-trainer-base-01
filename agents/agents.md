# Agents — Agentic Context

This folder provides context for AI agents (Antigravity, Codex, etc.) working in this repo.

## Repo Purpose
LLM finetuning experimentation — understanding model behaviors, input/output formats, LoRA/QLoRA techniques at 7-8B scale (Llama 3.1 8B, Mistral 7B).

## Agent Conventions

### File Roles
| File | Purpose |
|------|---------|
| `agents.md` | This file. Agentic context and conventions |
| `adr_log.md` | Timestamped decision/action log (append-only) |
| `to_vamsi.md` | High-signal comms to Vamsi (sparse, important only) |

### Principles
1. **Don't over-build** — Vamsi wants standalone control first, framework later
2. **Log decisions** — append to `adr_log.md` with timestamp, context, decision
3. **Keep scripts standalone** — each script in `scripts/` should be runnable independently
4. **Small footprint** — no large files in repo; symlink to central cache
5. **Communicate sparingly** — `to_vamsi.md` is for truly important observations only

### Models of Interest
- `meta-llama/Llama-3.1-8B-Instruct`
- `mistralai/Mistral-7B-v0.1` / `mistralai/Mistral-7B-Instruct-v0.3`

### Environment
- **Conda env**: `finetune_base_env` — activate via `conda activate finetune_base_env`
- **direnv**: This repo uses `direnv` to auto-load `.envrc` on `cd` into the project. Env vars, path adjustments, and conda activation are managed there.

### HF Cache
Using default HF cache (`~/.cache/huggingface`). Can centralize later via `HF_HOME` env var if needed.

### Tech Stack
- `transformers` + `tokenizers` — model loading, inference
- `peft` — LoRA/QLoRA adapters
- `bitsandbytes` — quantization
- `trl` — SFTTrainer for finetuning
- `datasets` — HF datasets
- `accelerate` — device management
