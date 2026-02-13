#!/usr/bin/env python3
"""
preview_sql_data.py — Download and preview the sql-create-context dataset.

Shows raw examples, formatted chat examples, and dataset statistics.

Usage:
    python scripts/preview_sql_data.py
"""

import sys
sys.path.insert(0, ".")

from datasets import load_dataset


def main():
    print("=" * 60)
    print("Downloading: b-mc2/sql-create-context")
    print("=" * 60)

    ds = load_dataset("b-mc2/sql-create-context", split="train")

    print(f"\nDataset size: {len(ds)} examples")
    print(f"Columns: {ds.column_names}")
    print(f"Features: {ds.features}")

    # --- Raw examples ---
    print("\n" + "=" * 60)
    print("RAW EXAMPLES (first 5)")
    print("=" * 60)

    for i in range(min(5, len(ds))):
        ex = ds[i]
        print(f"\n--- Example {i + 1} ---")
        for key, val in ex.items():
            val_str = str(val)
            if len(val_str) > 300:
                val_str = val_str[:300] + "..."
            print(f"  {key}: {val_str}")

    # --- How it would look as chat training data ---
    print("\n" + "=" * 60)
    print("FORMATTED AS CHAT (how the model will see it)")
    print("=" * 60)

    for i in range(min(3, len(ds))):
        ex = ds[i]
        context = ex.get("context", "")
        question = ex.get("question", "")
        answer = ex.get("answer", "")

        user_msg = f"Given the following SQL table schema:\n\n{context}\n\nWrite a SQL query to answer: {question}"
        assistant_msg = answer

        print(f"\n--- Training Example {i + 1} ---")
        print(f"[USER]: {user_msg}")
        print(f"[ASSISTANT]: {assistant_msg}")

    # --- Stats ---
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)

    # Answer lengths
    answer_lengths = [len(ex["answer"]) for ex in ds]
    print(f"Answer length (chars): min={min(answer_lengths)}, max={max(answer_lengths)}, "
          f"avg={sum(answer_lengths)/len(answer_lengths):.0f}")

    # Question lengths
    question_lengths = [len(ex["question"]) for ex in ds]
    print(f"Question length (chars): min={min(question_lengths)}, max={max(question_lengths)}, "
          f"avg={sum(question_lengths)/len(question_lengths):.0f}")

    # Context lengths
    context_lengths = [len(ex.get("context", "")) for ex in ds]
    print(f"Context length (chars): min={min(context_lengths)}, max={max(context_lengths)}, "
          f"avg={sum(context_lengths)/len(context_lengths):.0f}")

    print(f"\nTotal examples: {len(ds)}")
    print("Recommended subset for finetuning: 1000 examples")
    print("Done!")


if __name__ == "__main__":
    main()
