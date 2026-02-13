#!/usr/bin/env python3
"""
train.py — Recipe-driven LoRA/QLoRA finetuning.

Loads a YAML recipe, sets up model + LoRA + dataset, trains via SFTTrainer,
and saves the adapter to outputs/lora/{tag}_{timestamp}/.

Usage:
    python scripts/train.py --recipe configs/training/llama31_lora_smoke.yaml
    python scripts/train.py --recipe configs/training/llama31_lora_smoke.yaml --data data/custom.jsonl
"""

import sys
import argparse
import logging

sys.path.insert(0, ".")

from src.config import load_recipe, get_device
from src.utils import (
    load_tokenizer,
    load_model,
    get_bnb_config_from_dict,
    prepare_dataset,
    create_output_dir,
    save_recipe_copy,
    print_device_info,
    print_model_stats,
)

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Recipe-driven LoRA finetuning")
    parser.add_argument(
        "--recipe", required=True,
        help="Path to YAML recipe file (e.g. configs/training/llama31_lora_smoke.yaml)",
    )
    parser.add_argument(
        "--data", default=None,
        help="Optional override: path to local data file (jsonl/json/csv). "
             "If not provided, uses the recipe's default_dataset from HF.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Load everything but skip actual training. Useful for smoke testing setup.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # --- Device info ---
    print("=" * 60)
    print("DEVICE INFO")
    print("=" * 60)
    print_device_info()
    device = get_device()
    print(f"Selected device: {device}")
    print()

    # --- Load recipe ---
    print("=" * 60)
    print(f"RECIPE: {args.recipe}")
    print("=" * 60)
    recipe = load_recipe(args.recipe)
    print(f"Tag:         {recipe.training_tag}")
    print(f"Description: {recipe.description}")
    print(f"Model:       {recipe.model.name}")
    print(f"LoRA rank:   {recipe.lora.r}")
    print(f"LoRA alpha:  {recipe.lora.lora_alpha}")
    print(f"Targets:     {recipe.lora.target_modules}")
    print(f"Epochs:      {recipe.training.num_train_epochs}")
    print(f"Batch size:  {recipe.training.per_device_train_batch_size}")
    print(f"LR:          {recipe.training.learning_rate}")
    print(f"fp16={recipe.training.fp16}, bf16={recipe.training.bf16}")
    print()

    # --- Create output directory ---
    output_dir = create_output_dir(recipe.training_tag)
    save_recipe_copy(args.recipe, output_dir)

    # --- Load tokenizer ---
    print("=" * 60)
    print("LOADING TOKENIZER")
    print("=" * 60)
    tokenizer = load_tokenizer(recipe.model)
    print(f"Vocab size: {tokenizer.vocab_size}")
    print(f"Pad token:  {tokenizer.pad_token} (id: {tokenizer.pad_token_id})")
    print()

    # --- Load model (with optional quantization) ---
    print("=" * 60)
    print("LOADING MODEL")
    print("=" * 60)
    quantization_config = None
    if recipe.quantization and device == "cuda":
        print("QLoRA quantization enabled (CUDA)")
        quantization_config = get_bnb_config_from_dict(recipe.quantization)
    elif recipe.quantization and device != "cuda":
        print("⚠ Quantization requested but skipped (requires CUDA, got {device})")

    model = load_model(recipe.model, quantization_config)
    print()

    # --- Apply LoRA ---
    print("=" * 60)
    print("APPLYING LoRA")
    print("=" * 60)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    if quantization_config:
        model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=recipe.lora.r,
        lora_alpha=recipe.lora.lora_alpha,
        lora_dropout=recipe.lora.lora_dropout,
        target_modules=recipe.lora.target_modules,
        bias=recipe.lora.bias,
        task_type=recipe.lora.task_type,
    )
    model = get_peft_model(model, peft_config)
    print_model_stats(model)
    print()

    # --- Prepare dataset ---
    print("=" * 60)
    print("PREPARING DATASET")
    print("=" * 60)
    dataset = prepare_dataset(recipe.data, tokenizer, data_path=args.data)
    print(f"Sample 0 preview:")
    text_field = recipe.data.text_field or "text"
    if text_field in dataset.column_names:
        sample = dataset[0][text_field]
        print(sample[:500] + ("..." if len(sample) > 500 else ""))
    print()

    # --- Dry run check ---
    if args.dry_run:
        print("=" * 60)
        print("DRY RUN — skipping training")
        print(f"Output dir: {output_dir}")
        print("=" * 60)
        return

    # --- Train ---
    print("=" * 60)
    print("TRAINING")
    print("=" * 60)
    from transformers import TrainingArguments
    from trl import SFTTrainer

    # Calculate warmup steps from ratio
    total_steps = (
        len(dataset) // recipe.training.per_device_train_batch_size
        // recipe.training.gradient_accumulation_steps
        * recipe.training.num_train_epochs
    )
    warmup_steps = int(total_steps * recipe.training.warmup_ratio)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=recipe.training.num_train_epochs,
        per_device_train_batch_size=recipe.training.per_device_train_batch_size,
        gradient_accumulation_steps=recipe.training.gradient_accumulation_steps,
        learning_rate=recipe.training.learning_rate,
        lr_scheduler_type=recipe.training.lr_scheduler_type,
        warmup_steps=warmup_steps,
        weight_decay=recipe.training.weight_decay,
        logging_steps=recipe.training.logging_steps,
        save_strategy=recipe.training.save_strategy,
        fp16=recipe.training.fp16,
        bf16=recipe.training.bf16,
        max_grad_norm=recipe.training.max_grad_norm,
        seed=recipe.training.seed,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    logger.info("Starting training...")
    train_result = trainer.train()

    # --- Save ---
    print("=" * 60)
    print("SAVING")
    print("=" * 60)
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir / "tokenizer"))

    # Save training metrics
    metrics_path = output_dir / "training_log.txt"
    with open(metrics_path, "w") as f:
        f.write(f"Recipe: {args.recipe}\n")
        f.write(f"Model: {recipe.model.name}\n")
        f.write(f"Tag: {recipe.training_tag}\n")
        f.write(f"Device: {device}\n\n")
        for key, val in train_result.metrics.items():
            f.write(f"{key}: {val}\n")

    print(f"Adapter saved to: {output_dir}")
    print(f"Metrics saved to: {metrics_path}")
    print("Done!")


if __name__ == "__main__":
    main()
