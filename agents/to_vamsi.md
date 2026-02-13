# To Vamsi — Agent Communications

> This file is for high-signal, important observations only. Agents should write here sparingly.

---

### 2026-02-11 — Scaffold Ready
The scaffold is set up. Using default HF cache (`~/.cache/huggingface`) for now.

1. **Hardware choice per experiment** — Scripts in `src/config.py` default to auto-detecting MPS/CUDA/CPU. QLoRA with `bitsandbytes` requires CUDA — won't work on Mac MPS. For Mac-local work, standard LoRA (fp16/bf16) or CPU inference is the path.
