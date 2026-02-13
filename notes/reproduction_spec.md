# Reproduction Spec — LoRA Finetuning System

> **Purpose:** Give another AI all the context needed to reproduce the `config → utils → train → inference` system from scratch. Copy this file into the other workspace as instructions.

---

## Architecture Overview

```
recipe.yaml        ← Declarative config (what to train, with what data, what hyperparams)
src/config.py       ← Parses YAML → typed Python dataclasses
src/utils.py        ← Model/tokenizer loading, dataset prep, formatting, output dir management
scripts/train.py    ← Orchestrator: calls config + utils + peft + trl to train & save adapter
scripts/inference.py ← Generation: loads base ± LoRA adapter, runs prompts, compares outputs
```

**External libraries used:**
- `transformers` — `AutoModelForCausalLM`, `AutoTokenizer`, `TrainingArguments`, `BitsAndBytesConfig`
- `peft` — `LoraConfig`, `get_peft_model`, `PeftModel`, `prepare_model_for_kbit_training`
- `trl` — `SFTTrainer` (the actual training loop)
- `datasets` — `load_dataset`, `Dataset`

---

## File 1: `config.py` — Configuration & Recipe Loading

### Responsibilities

1. **Device detection** — `get_device()` returns `"cuda"` / `"mps"` / `"cpu"` based on `torch.cuda.is_available()` and `torch.backends.mps.is_available()`

2. **Dtype selection** — `get_dtype(device)` returns `bfloat16` for CUDA, `float16` for MPS, `float32` for CPU. This controls what dtype the model is *loaded* in (not trained in).

3. **Dataclass definitions** — Typed config objects, all with sensible defaults:
   - `ModelConfig` — `name`, `device`, `dtype`, `trust_remote_code`, `max_seq_length`
   - `LoRAConfig` — `r`, `lora_alpha`, `lora_dropout`, `target_modules` (list of layer names), `bias`, `task_type`
   - `QLoRAConfig(LoRAConfig)` — extends LoRA with bitsandbytes 4-bit quantization settings (CUDA only)
   - `TrainingConfig` — all training hyperparams: `epochs`, `batch_size`, `gradient_accumulation_steps`, `learning_rate`, `lr_scheduler_type`, `warmup_ratio`, `weight_decay`, `logging_steps`, `save_strategy`, `fp16`, `bf16`, `max_grad_norm`, `seed`
   - `DataConfig` — `default_dataset` (HF Hub ID), `text_field`, `max_samples`, `format` (`"sql"` / `"alpaca"` / `None`)
   - `Recipe` — container holding all the above + `training_tag`, `description`, `quantization` dict, `raw` YAML dict

4. **`load_recipe(path)` — the main function:**
   - Reads YAML with `yaml.safe_load()`
   - Creates each config object from the YAML sections
   - **CRITICAL: Auto-adjusts fp16/bf16 based on detected device:**
     - CUDA → `fp16=False, bf16=True`
     - MPS or CPU → `fp16=False, bf16=False` (trains in float32)
   - Returns a `Recipe` object

### ⚠️ Gotchas for Reproduction
- MPS does NOT support AMP/mixed-precision training. If you set `fp16=True` on MPS, training will NaN-explode around step 30. The model *loads* in float16 (for memory), but the training itself must run in float32.
- The `target_modules` list in LoRA config determines which layers get adapters. For Llama models, the standard set is `["q_proj", "k_proj", "v_proj", "o_proj"]`. Including `gate_proj`, `up_proj`, `down_proj` adds more trainable params.

---

## File 2: `utils.py` — Shared Utilities

### Responsibilities

**Section A: Model & Tokenizer Loading**

1. **`load_tokenizer(model_config)`** — Calls `AutoTokenizer.from_pretrained(model_config.name)`. Sets `pad_token = eos_token` if pad_token is None (required for batched training).

2. **`load_model(model_config, quantization_config=None)`** — Calls `AutoModelForCausalLM.from_pretrained()` with `torch_dtype=model_config.dtype` and `device_map=model_config.device`. If quantization_config is provided, passes that and uses `device_map="auto"` instead.

3. **`load_model_with_lora(model_name, lora_path, device=None)`** — For inference: loads the base model, then wraps it with `PeftModel.from_pretrained(model, lora_path)`. Returns `(model, tokenizer)`. This is how you load a previously-trained adapter for inference.

4. **`get_bnb_config_from_dict(quant_dict)`** — Converts a recipe's quantization dict to a `BitsAndBytesConfig`. Only used on CUDA.

**Section B: Dataset Preparation**

5. **`prepare_dataset(data_config, tokenizer, data_path=None)`** — The main data pipeline:
   - **Load**: From local file (`.jsonl` / `.json` / `.csv`) if `data_path` given, otherwise from HF Hub using `data_config.default_dataset`
   - **Truncate**: If `max_samples` is set, take first N samples
   - **Format**: If `text_field` is None, auto-detect format and apply chat template formatting:
     - For `format="sql"` → calls `_format_sql_to_chat()`
     - For `format="alpaca"` → calls `_format_alpaca_to_chat()`
     - Auto-detection: if columns include `context` + `answer` → sql, if `instruction` → alpaca
   - **Returns**: HF `Dataset` with a single `"text"` column ready for SFTTrainer

6. **`_format_sql_to_chat(example, tokenizer)`** — The SQL formatter:
   - Input: `{"context": "CREATE TABLE...", "question": "...", "answer": "SELECT..."}`
   - Builds user message: `"Given the following SQL table schema:\n\n{context}\n\nWrite a SQL query to answer: {question}"`
   - Builds assistant message: `"{answer}"` (just the raw SQL, no explanation)
   - Applies tokenizer's chat template (e.g., Llama's `<|begin_of_text|>` format)
   - Returns `{"text": formatted_string}`
   - **THIS IS THE MOST IMPORTANT FUNCTION** — the assistant response in training data being pure SQL is what teaches the model to output only SQL

7. **`_format_alpaca_to_chat(example, tokenizer)`** — Alternative formatter for alpaca-style data (`instruction`, `input`, `output` fields)

**Section C: Output & Helpers**

8. **`create_output_dir(training_tag)`** — Creates `outputs/lora/{tag}_{YYYYMMDD_HHMMSS}/`
9. **`save_recipe_copy(recipe_path, output_dir)`** — Copies YAML into output dir for reproducibility
10. **`print_device_info()`** — Prints CUDA/MPS availability
11. **`print_model_stats(model)`** — Prints total params vs trainable params (important to verify LoRA is applied correctly)
12. **`format_chat_prompt(tokenizer, messages, add_generation_prompt=True)`** — For inference: applies chat template to a list of messages. With `add_generation_prompt=True`, adds the assistant header tag so the model knows to start generating.

---

## File 3: `train.py` — Training Orchestrator

### Responsibilities (in execution order)

1. **Parse CLI args**: `--recipe` (required), `--data` (optional local override), `--dry-run` (skip training)

2. **Print device info** → calls `print_device_info()` and `get_device()`

3. **Load recipe** → calls `load_recipe(args.recipe)` → gets typed `Recipe` object

4. **Create output dir** → calls `create_output_dir(recipe.training_tag)` + `save_recipe_copy()`

5. **Load tokenizer** → calls `load_tokenizer(recipe.model)`

6. **Load model** → calls `load_model(recipe.model, quantization_config)`. Quantization only applied on CUDA.

7. **Apply LoRA** (this is where peft comes in):
   - If quantized: `prepare_model_for_kbit_training(model)` first
   - Create `LoraConfig(r, alpha, dropout, target_modules, bias, task_type)` from recipe
   - `model = get_peft_model(model, peft_config)` — freezes base, adds adapters
   - Print stats to verify: should show ~8B frozen + ~13M trainable

8. **Prepare dataset** → calls `prepare_dataset(recipe.data, tokenizer, data_path)`. Returns Dataset with `"text"` column.

9. **Calculate warmup steps**: `total_steps = (len(dataset) // batch_size // grad_accum) * epochs`, then `warmup_steps = int(total_steps * warmup_ratio)`

10. **Create TrainingArguments** from recipe's training config — must include `report_to="none"` to skip Wandb/MLflow

11. **Create SFTTrainer** with: `model`, `args`, `train_dataset`, `processing_class=tokenizer`. (Note: older trl versions use `tokenizer=` kwarg and `dataset_text_field="text"`. Newer versions use `processing_class=` and auto-detect.)

12. **`trainer.train()`** — runs the full training loop (forward → loss → backward → optimizer step, with logging)

13. **Save**:
    - `trainer.save_model(output_dir)` — saves `adapter_model.safetensors` + `adapter_config.json` (~55MB for LoRA, NOT the full 16GB model)
    - `tokenizer.save_pretrained(output_dir / "tokenizer")`
    - Writes `training_log.txt` with final metrics from `train_result.metrics`

### Output Structure
```
outputs/lora/llama31-sql_20260211_233824/
├── adapter_model.safetensors    ← LoRA weights (~55MB)
├── adapter_config.json          ← LoRA config (r, alpha, targets)
├── recipe.yaml                  ← Copy of input recipe
├── training_log.txt             ← Final metrics
├── tokenizer/                   ← Saved tokenizer
└── checkpoint-375/              ← Intermediate checkpoint with trainer_state.json
```

---

## File 4: `inference.py` — Inference & Comparison

### Responsibilities

1. **Parse CLI args**: `--model` (HF ID, required), `--lora-path` (adapter dir, optional), `--compare` (side-by-side mode), `--prompts-file`, `--max-new-tokens`, `--temperature`, `--save`

2. **Load models** — three modes:
   - Base only: `load_model()` + `load_tokenizer()`
   - Base + LoRA: `load_model_with_lora(model_name, lora_path)`
   - Compare mode: loads BOTH (base AND base+LoRA separately)

3. **Get prompts**: from `--prompts-file` or built-in defaults. Supports multi-line prompts separated by `\n---\n` (for SQL schemas)

4. **`generate(model, tokenizer, prompt, max_new_tokens, temperature, device)`**:
   - Wraps prompt as `[{"role": "user", "content": prompt}]`
   - Applies tokenizer's chat template with `add_generation_prompt=True` (adds assistant header)
   - Tokenizes → moves to device
   - `model.generate(**inputs, max_new_tokens, temperature, do_sample, pad_token_id)`
   - Decodes only NEW tokens (strips the input prefix): `outputs[0][inputs["input_ids"].shape[1]:]`

5. **`run_comparison()`**: runs each prompt through both models, prints side-by-side, collects results

6. **Save**: optionally writes results to `outputs/inference/comparison_{timestamp}.json`

### Prompts File Format
```
Given the following SQL table schema:

CREATE TABLE employees (id INT, name VARCHAR, salary FLOAT)

Write a SQL query to answer: Which employees earn over 80000?
---
Given the following SQL table schema:

CREATE TABLE orders (id INT, customer VARCHAR, total FLOAT, date DATE)

Write a SQL query to answer: What is the total revenue for January 2024?
```

---

## Recipe YAML Format

```yaml
training_tag: "llama31-sql"
description: "LoRA finetuning for text-to-SQL"

model:
  name: "meta-llama/Llama-3.1-8B-Instruct"
  max_seq_length: 512

lora:
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules: ["q_proj", "k_proj", "v_proj", "o_proj"]
  bias: "none"
  task_type: "CAUSAL_LM"

training:
  num_train_epochs: 3
  per_device_train_batch_size: 2
  gradient_accumulation_steps: 4
  learning_rate: 5.0e-5
  lr_scheduler_type: "cosine"
  warmup_ratio: 0.06
  weight_decay: 0.01
  logging_steps: 10
  save_strategy: "epoch"
  max_grad_norm: 0.3
  seed: 42

data:
  default_dataset: "b-mc2/sql-create-context"
  max_samples: 1000
  format: "sql"
```

---

## Dependencies (requirements.txt)

```
torch>=2.1.0
transformers>=4.36.0
peft>=0.7.0
trl>=0.7.0
datasets>=2.14.0
bitsandbytes>=0.41.0    # CUDA only, skip on MPS
accelerate>=0.25.0
pyyaml
```

---

## Quality Checklist — Verify These Match

After reproduction, run these checks:

| Check | Expected |
|-------|----------|
| `print_model_stats()` after `get_peft_model()` | ~8B total, ~13.6M trainable (~0.17%) |
| Training loss at step 10 | ~2.5-3.0 |
| Training loss at step 375 | ~0.3-0.6 |
| Token accuracy final | ~85-90% |
| `fp16` on MPS | Must be `False` — verify in loaded recipe |
| Adapter size on disk | ~50-60MB |
| LoRA model inference output | Pure SQL, no explanation |
| Base model inference output | SQL wrapped in explanation text |

---

## Critical Gotchas

1. **fp16 on MPS = DEATH.** Model loads in float16 but trains in float32. Auto-detect this in config.py.
2. **pad_token** must be set. Most LLMs don't have one — set `pad_token = eos_token`.
3. **SFTTrainer API changed** between trl versions. Older: `tokenizer=tokenizer, dataset_text_field="text"`. Newer: `processing_class=tokenizer` (auto-detects text column).
4. **Loss masking**: SFTTrainer only computes loss on assistant tokens, not the user prompt. This is automatic — you don't need to implement masking yourself.
5. **Chat template matters**: The prompt format at inference must match what was used in training. Both use `tokenizer.apply_chat_template()` so they stay in sync automatically.
6. **Generate decoding**: When decoding, strip the input tokens: `new_tokens = outputs[0][inputs["input_ids"].shape[1]:]`. Otherwise you'll echo the prompt.
