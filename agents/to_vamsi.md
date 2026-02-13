# To Vamsi — Agent Communications

> This file is for high-signal, important observations only. Agents should write here sparingly.

---

### 2026-02-11 — Scaffold Ready
The scaffold is set up. Before diving into scripts, two things worth pinning down:

1. **HF cache env var** — Run `export HF_HOME=/Users/vamsi/01_BUILD/_meta/models` (add to `.zshrc` or `.env`) before any `transformers` model downloads. This routes all HF downloads to a single central location.

2. **Hardware choice per experiment** — Scripts in `src/config.py` default to auto-detecting MPS/CUDA/CPU. QLoRA with `bitsandbytes` requires CUDA — won't work on Mac MPS. For Mac-local work, standard LoRA (fp16/bf16) or CPU inference is the path.
