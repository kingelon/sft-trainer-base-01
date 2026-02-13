# Scripts

Standalone experiment scripts. Numbered for natural progression.

| # | Script | Purpose |
|---|--------|---------|
| 01 | `01_explore_tokenizer.py` | Tokenizer inspection, chat template comparison |
| 02 | `02_base_inference.py` | Base model inference baselines |
| 03 | `03_prepare_dataset.py` | Dataset loading, formatting, tokenization |
| 04 | `04_finetune_lora.py` | LoRA/QLoRA finetuning |
| 05 | `05_eval_finetuned.py` | Compare base vs finetuned outputs |

Each script is self-contained. Use `from src.config import ...` for shared settings.
