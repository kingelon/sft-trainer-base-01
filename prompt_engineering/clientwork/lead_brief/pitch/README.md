# Pitch Component

> Generates a 3–5 sentence sales pitch paragraph + conversation opener from lead data.

## Current Prompt

→ [prompt_v1_structured.md](prompt_v1_structured.md)

**Architecture:** Role → Objective → Card Knowledge → Pseudo-code Selection Logic → Pitch Rules → 7 Few-Shot Examples → Input/Output Format

**Key features:**
- Structured reasoning (model shows card selection logic before writing)
- No-negative-framing constraint (never criticize existing AMEX cards)
- Natural "rep talk" tone enforcement
- Verified card benefits from AMEX website

## Scenarios Covered

| # | Scenario | Recommended Card |
|---|---|---|
| 1 | Revenue < $4M + existing consumer AMEX | Business Platinum |
| 2 | Revenue ≥ $10M + no AMEX + large team | Corporate Platinum |
| 3 | $4M–$10M + Very High Corp propensity | Corporate Platinum |
| 4 | $4M–$10M + High Corp propensity | Corporate Gold |
| 5 | $4M–$10M + Neutral Corp propensity | Corporate Green |
| 6 | $4M–$10M + OPEN propensity | Business Gold |
| 7 | No revenue + no propensity | Business Gold (catch-all) |

## Context Files

| File | Purpose |
|---|---|
| [card_catalog.md](context/card_catalog.md) | Full card product catalog (fees, benefits, best-fit signals) |
| [decision_logic.md](context/decision_logic.md) | Original decision tree for card selection |
| [sales_methodology.md](context/sales_methodology.md) | AMEX questioning funnel and sales approach |

## Iteration History

| Version | File | Notes |
|---|---|---|
| v0 | [v0_system_prompt.md](_iterations/v0_system_prompt.md) | Original long-form prompt |
| v0.1 | [v0_concise_5line.md](_iterations/v0_concise_5line.md) | Condensed to 5-line structure |
| v1 | [v1_propensity.md](_iterations/v1_propensity.md) | Added propensity buckets, AO name, card comparison |
| **v1 (current)** | [prompt_v1_structured.md](prompt_v1_structured.md) | Structured reasoning, verified benefits, 7 scenarios |
