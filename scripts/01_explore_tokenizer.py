#!/usr/bin/env python3
"""
01 — Explore Tokenizer

Compare tokenizers for Llama 3.1 8B and Mistral 7B:
- Vocabulary size and special tokens
- Chat template formatting
- Token-level encoding differences

Usage:
    python scripts/01_explore_tokenizer.py
"""

# TODO: Implement when ready to explore tokenizer behaviors
# See docs/model_notes.md for known chat template formats

import sys
sys.path.insert(0, ".")

from src.config import LLAMA_31_8B, MISTRAL_7B_INSTRUCT
from src.utils import load_tokenizer, format_chat_prompt

if __name__ == "__main__":
    print("Script stub — implement when ready")
    print(f"Target models: {LLAMA_31_8B.name}, {MISTRAL_7B_INSTRUCT.name}")
