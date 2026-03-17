# Lead Brief — Prompt Engineering Project

> Client work project for generating AI-powered lead briefing components.
> Each component has its own prompt, context, examples, and iteration history.

## Project Structure

```
lead_brief/
├── README.md              ← you are here
├── _schema/               ← shared data field definitions (used across all components)
│   └── input_fields.md
├── _docs/                 ← requirements, planning, client communication
│   └── requirements_open_items.md
├── pitch/                 ← sales pitch generation
│   ├── prompt_v1_structured.md   ← CURRENT production prompt
│   ├── context/                  ← card catalog, decision logic, methodology
│   ├── examples/                 ← sample outputs, few-shot references
│   └── _iterations/              ← version history of prompt evolution
├── lead_summary/          ← [future] structured lead summary generation
└── why_good_lead/         ← [future] lead qualification reasoning
```

## Quick Access — Active Prompts

| Component | Current Prompt | Status |
|---|---|---|
| **Pitch** | [prompt_v1_structured.md](pitch/prompt_v1_structured.md) | ✅ Active — 7 scenarios, structured reasoning, verified card benefits |
| **Lead Summary** | — | 🔲 Not started |
| **Why Good Lead** | [prompt_v1_why_good_lead.md](why_good_lead/prompt_v1_why_good_lead.md) | ✅ Active — production prompt, 7 examples, signal-driven |

## How Components Work

Each component folder follows the same pattern:

```
component/
├── prompt_v{N}_{name}.md   ← current production prompt
├── context/                 ← reference material the prompt draws from
├── examples/                ← sample inputs/outputs for testing and few-shot
└── _iterations/             ← older prompt versions (git tracks full history)
```

- **Prompts** are self-contained — copy below the first `---` into ChatGPT/API
- **Context/** holds domain knowledge files the prompt references
- **Examples/** has sample outputs and testing scenarios
- **_iterations/** stores previous prompt versions for reference and rollback

## Shared Data Fields

All components consume the same lead data input. See [_schema/input_fields.md](_schema/input_fields.md) for the full field catalog covering CRM fields, derived signals, and propensity data.

## Key Business Rules (cross-component)

| Rule | Value |
|---|---|
| Revenue < $4M | → Business Platinum |
| Revenue $4M–$10M | → Propensity-driven (see routing logic) |
| Revenue ≥ $10M | → Corporate Platinum |
| No revenue, no propensity | → Business Gold (catch-all) |
| Propensity: Very High Corp | → Corporate Platinum |
| Propensity: High Corp | → Corporate Gold |
| Propensity: Neutral Corp | → Corporate Green |
| Propensity: OPEN | → Business Gold |

## Adding a New Component

1. Create a folder: `lead_brief/{component_name}/`
2. Add: `prompt_v1_{name}.md`, `context/`, `examples/`, `_iterations/`
3. Register it in the Quick Access table above
4. Ensure input JSON matches [_schema/input_fields.md](_schema/input_fields.md) — extend if needed
