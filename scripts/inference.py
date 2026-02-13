#!/usr/bin/env python3
"""
inference.py — Run inference with optional LoRA adapter, with comparison mode.

Usage:
    # Base model only
    python scripts/inference.py --model meta-llama/Llama-3.1-8B-Instruct

    # Base + LoRA
    python scripts/inference.py --model meta-llama/Llama-3.1-8B-Instruct \\
        --lora-path outputs/lora/llama31-smoke_20260211_175400

    # Side-by-side comparison (base vs base+LoRA)
    python scripts/inference.py --model meta-llama/Llama-3.1-8B-Instruct \\
        --lora-path outputs/lora/llama31-smoke_20260211_175400 --compare

    # With prompts from file
    python scripts/inference.py --model meta-llama/Llama-3.1-8B-Instruct \\
        --prompts-file data/test_prompts.txt
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, ".")

from src.config import ModelConfig, get_device, get_dtype
from src.utils import (
    load_model,
    load_tokenizer,
    load_model_with_lora,
    format_chat_prompt,
    print_device_info,
    print_model_stats,
)

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Inference with optional LoRA")
    parser.add_argument(
        "--model", required=True,
        help="HF model ID or local path (e.g. meta-llama/Llama-3.1-8B-Instruct)",
    )
    parser.add_argument(
        "--lora-path", default=None,
        help="Path to LoRA adapter directory (e.g. outputs/lora/llama31-smoke_...)",
    )
    parser.add_argument(
        "--compare", action="store_true",
        help="Run prompts through both base AND base+LoRA, show side-by-side",
    )
    parser.add_argument(
        "--prompts-file", default=None,
        help="Path to a text file with one prompt per line",
    )
    parser.add_argument(
        "--max-new-tokens", type=int, default=256,
        help="Max tokens to generate (default: 256)",
    )
    parser.add_argument(
        "--temperature", type=float, default=0.7,
        help="Sampling temperature (default: 0.7)",
    )
    parser.add_argument(
        "--save", action="store_true",
        help="Save outputs to outputs/inference/",
    )
    return parser.parse_args()


def generate(model, tokenizer, prompt: str, max_new_tokens: int, temperature: float, device: str) -> str:
    """Generate a response from a model given a prompt."""
    messages = [{"role": "user", "content": prompt}]
    formatted = format_chat_prompt(tokenizer, messages, add_generation_prompt=True)

    inputs = tokenizer(formatted, return_tensors="pt").to(device)

    with __import__("torch").no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.pad_token_id,
        )

    # Decode only the new tokens
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def run_interactive(model, tokenizer, args, device: str, label: str = ""):
    """Interactive prompt loop."""
    print(f"\n{'=' * 60}")
    print(f"Interactive mode{f' [{label}]' if label else ''}")
    print("Type your prompt and press Enter. Type 'quit' to exit.")
    print(f"{'=' * 60}\n")

    while True:
        try:
            prompt = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if prompt.lower() in ("quit", "exit", "q"):
            break
        if not prompt:
            continue

        response = generate(model, tokenizer, prompt, args.max_new_tokens, args.temperature, device)
        print(f"\n{response}\n")


def run_comparison(base_model, base_tokenizer, lora_model, lora_tokenizer,
                   prompts: list, args, device: str) -> list:
    """Run same prompts through base and LoRA models, show side-by-side."""
    results = []

    for i, prompt in enumerate(prompts):
        print(f"\n{'=' * 60}")
        print(f"PROMPT {i + 1}: {prompt}")
        print(f"{'=' * 60}")

        base_response = generate(
            base_model, base_tokenizer, prompt,
            args.max_new_tokens, args.temperature, device,
        )
        print(f"\n--- BASE MODEL ---")
        print(base_response)

        lora_response = generate(
            lora_model, lora_tokenizer, prompt,
            args.max_new_tokens, args.temperature, device,
        )
        print(f"\n--- BASE + LoRA ---")
        print(lora_response)

        results.append({
            "prompt": prompt,
            "base_response": base_response,
            "lora_response": lora_response,
        })

    return results


def get_prompts(args) -> list:
    """Get prompts from file or default test set.

    Prompts file supports two formats:
    - One prompt per line (simple)
    - Multi-line prompts separated by '---' (for SQL schemas etc.)
    """
    if args.prompts_file:
        with open(args.prompts_file) as f:
            content = f.read()

        # Check if file uses --- separator for multi-line prompts
        if "\n---\n" in content:
            prompts = [p.strip() for p in content.split("\n---\n") if p.strip()]
        else:
            prompts = [line.strip() for line in content.splitlines() if line.strip()]

        return prompts

    # Default test prompts
    return [
        "What is the capital of France?",
        "Explain quantum computing in simple terms.",
        "Write a short poem about machine learning.",
        "What are the key differences between Python and JavaScript?",
    ]


def main():
    args = parse_args()
    device = get_device()

    print_device_info()
    print()

    if args.compare:
        if not args.lora_path:
            print("ERROR: --compare requires --lora-path")
            sys.exit(1)

        # Load base model
        print("Loading BASE model...")
        model_config = ModelConfig(name=args.model)
        base_model = load_model(model_config)
        base_tokenizer = load_tokenizer(model_config)
        print_model_stats(base_model)

        # Load LoRA model
        print("\nLoading BASE + LoRA model...")
        lora_model, lora_tokenizer = load_model_with_lora(args.model, args.lora_path, device)
        print_model_stats(lora_model)

        # Run comparison
        prompts = get_prompts(args)
        results = run_comparison(
            base_model, base_tokenizer,
            lora_model, lora_tokenizer,
            prompts, args, device,
        )

        # Save if requested
        if args.save:
            out_dir = Path("outputs/inference")
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = out_dir / f"comparison_{ts}.json"
            with open(out_file, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {out_file}")

    else:
        # Single model mode
        if args.lora_path:
            print(f"Loading model + LoRA: {args.model} + {args.lora_path}")
            model, tokenizer = load_model_with_lora(args.model, args.lora_path, device)
            label = "base+LoRA"
        else:
            print(f"Loading base model: {args.model}")
            model_config = ModelConfig(name=args.model)
            model = load_model(model_config)
            tokenizer = load_tokenizer(model_config)
            label = "base"

        print_model_stats(model)

        if args.prompts_file:
            # Batch mode from file
            prompts = get_prompts(args)
            results = []
            for i, prompt in enumerate(prompts):
                print(f"\n--- Prompt {i + 1}: {prompt}")
                response = generate(model, tokenizer, prompt, args.max_new_tokens, args.temperature, device)
                print(response)
                results.append({"prompt": prompt, "response": response})

            if args.save:
                out_dir = Path("outputs/inference")
                out_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_file = out_dir / f"inference_{label}_{ts}.json"
                with open(out_file, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"\nResults saved to: {out_file}")
        else:
            # Interactive mode
            run_interactive(model, tokenizer, args, device, label)


if __name__ == "__main__":
    main()
