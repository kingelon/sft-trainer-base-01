# Sale Pitch — Batch Pitch Generation for AMEX SME/Corporate Leads

## Architecture

```
Lead Data (CRM row) → Signal Extraction → Card-Lead Matching → System Prompt + Few-Shots → LLM → Pitch
```

## Files

| File | Purpose |
|---|---|
| `context.md` | All extracted knowledge: cards, methodology, signals |
| `card_catalog.md` | Structured product catalog (Business + Corporate) |
| `decision_logic.md` | Signal-to-card mapping rules (the decision tree) |
| `input_schema.md` | What fields come from CRM, what signals are derived |
| `system_prompt.md` | The production prompt template |
| `examples.md` | 4 worked pitch versions for demo/discussion |

## Usage

1. Read `input_schema.md` to understand what data is needed
2. Apply `decision_logic.md` to derive signals and match card
3. Feed the lead data + matched card into `system_prompt.md`
4. Send to any LLM (GPT-4, Claude, Gemini) → get pitch
