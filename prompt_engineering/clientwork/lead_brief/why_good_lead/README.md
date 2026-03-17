# Why Good Lead Component

> **Status:** ✅ Production prompt stored

Generates a concise, opportunity-focused summary explaining why a lead is a good prospect for commercial credit and charge card solutions. Output is a single paragraph (2–4 lines) read by sales reps immediately before outreach.

## Current Prompt

| File | Description |
|---|---|
| [prompt_v1_why_good_lead.md](prompt_v1_why_good_lead.md) | **Production prompt (pinned)** — 7 few-shot examples, priority-ordered signal inclusion |

## What the Prompt Covers

The production prompt surfaces (in priority order):
1. **Amex Card Relationship** — active cards, spend, AO ownership attribution
2. **Hot Signals** — internal digital signals, CXO changes, engagement indicators

## Output Characteristics

- One paragraph, 2–4 lines, plain natural language
- Signal-driven: strengths and context only, never frames around what's missing
- Strict: no fabrication, no absence references, no benchmarks

## Dependencies

- Shared input schema: [_schema/input_fields.md](../_schema/input_fields.md)
- May reference: [pitch/context/decision_logic.md](../pitch/context/decision_logic.md)
