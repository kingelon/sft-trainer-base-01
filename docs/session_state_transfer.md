# Session State Transfer — Lead Brief Intelligence

> **Purpose:** Carry-forward document for any future session. Contains the full accumulated context from the fine-tuning POC exploration, presentation, and next-phase planning.
> **Last updated:** 2026-03-04

---

## 1. The Use Case

**Client:** American Express
**Task:** "Why is this a good lead?" — generate structured lead briefs for sales reps from JSON data
**Core problem:** Given a complex JSON with company, card, spend, and intent data → produce a concise, consistently structured summary that a sales rep can read before a call

### What the brief needs to contain (in order)
1. **Company overview** — name, industry, revenue range, relationship tenure
2. **Card portfolio summary** — which cards (Delta SkyMiles, Business Blue Cash, Corporate Card, etc.), type counts
3. **Spend highlights** — total annual, top categories, YoY changes
4. **Intent signals** — hiring activity, acquisitions, C-suite changes, contact designation changes
5. **Recommended actions** — what the rep should lead with

### Input data fields available in the JSON
| Category | Fields |
|----------|--------|
| **Company Profile** | Company name, industry, revenue range, member history, relationship tenure |
| **Card Portfolio** | Multiple cards per account — Delta SkyMiles, Business Blue Cash, Corporate Card — each with card type (CA type), annual spend, category breakdown |
| **Spend Metrics** | Total annual spend, spend by category, YoY changes, average transaction size |
| **Intent Signals** | Hiring activity, acquisition signals, C-suite changes, primary contact designation changes |
| **Contact & Relationship** | Primary contact role, member history, prior interactions, product usage |

---

## 2. What We Built (POC)

### Architecture
```
YAML recipe → config.py → utils.py → train.py (TRL SFTTrainer + PEFT LoRA)
                                           ↓
                                    LoRA adapter saved (~55MB)
                                           ↓
                              merge script → merged model
                                           ↓
                              FastAPI serving → chatbot UI
```

### Key Files
| File | Purpose |
|------|---------|
| `configs/training/*.yaml` | Recipe-driven experiment configs |
| `src/config.py` | Dataclasses for model, LoRA, training, data configs; `load_recipe()` |
| `src/utils.py` | Model/tokenizer loading, dataset prep, Alpaca formatters |
| `scripts/train.py` | LoRA fine-tuning with SFTTrainer |
| `scripts/inference.py` | Inference with base vs fine-tuned comparison mode |

### Training Details
- **Base model:** Llama 3.1 8B Instruct
- **Method:** LoRA (rank 16, 7 target modules: q, k, v, o, gate, up, down)
- **Trainable params:** 13.6M / 8B total (0.17%)
- **Adapter size on disk:** ~55 MB
- **Training data:** ~200 synthetic examples (generated using the long prompt approach)
- **Infrastructure:** On-prem GPU

### How Training Data Was Created
Used the base model with a long detailed prompt (Approach A — ~2000+ tokens with formatting rules and few-shot examples) to generate ~200 structured briefs. These outputs became the supervised training examples. Fine-tuning then compresses that behavior into the adapter so it works with just a short prompt (~50 tokens).

---

## 3. What We Observed

### Approach A: Prompt + Few-Shot Examples
- Long prompt with formatting rules + 2–3 input/output example pairs
- **Produces structured output** — but ~2000+ tokens per call
- Consistency across varied inputs uncertain at scale

### Approach B: Base Model with Prompt Only
- Short instruction, no examples
- Output is verbose, free-form, section ordering varies per run
- Sections in different orders, fields omitted or paraphrased loosely

### Approach C: Fine-tuned Model (LoRA)
- Short prompt (~50 tokens) → structured output matching Approach A quality
- Consistent section ordering, consistent phrasing
- **Honest gap:** Number accuracy at ~85% with unvetted synthetic data → post-check step catches this

### The Key Insight
> Fine-tuning doesn't teach the model new facts about leads — it teaches the model how to consistently format what it's given. The adapter learns **formatting patterns** (which fields come first, how to phrase numbers, section structure) — not new factual knowledge.

---

## 4. Verified Industry References

These are the only three we can cite with confidence — all publicly accessible:

| Case | What Happened | Result | Source |
|------|--------------|--------|--------|
| **LoRA Land** (Predibase, 2024) | Fine-tuned 310 models with 4-bit LoRA across 31 tasks; deployed 25 Mistral-7B adapters on 1 A100 | Beat GPT-4 by 10 points on average | [arxiv.org/abs/2405.00732](https://arxiv.org/abs/2405.00732) |
| **CFM** (Hedge Fund, 2024) | Used Llama 70B for labeling, then fine-tuned 90M GLiNER for financial NER | 93.4% F1 (beat Llama 70B's 92.7%), 16–80× cheaper | [huggingface.co/blog/cfm-case-study](https://huggingface.co/blog/cfm-case-study) |
| **LoRA Paper** (Microsoft, 2021) | Tested LoRA on GPT-3 175B, RoBERTa, DeBERTa, GPT-2 | 10,000× fewer params, 3× less memory, same quality | [arxiv.org/abs/2106.09685](https://arxiv.org/abs/2106.09685) |

> **Warning:** Earlier versions of the presentation cited JPMorgan COiN, STL Digital, and Deepgram — these were NOT about fine-tuning specifically and had unverifiable URLs. They were removed and replaced with the above.

---

## 5. The "Product Sense" Framework

Learned from a colleague's Signal Beacon presentation (WTS — "When To Stop" use case with call transcripts). The 6-step pattern:

1. **Define the business problem** precisely (not the ML task)
2. **Decompose into measurable signals** (what data tells us something)
3. **Design a scoring/output framework** (how signals become decisions)
4. **Specify validation layers** (how to know if output is correct)
5. **Present with data-backed rationale** (not proposals — evidence)
6. **Propose next steps grounded in what's built** (not aspirational)

Key lesson: *think through the use case and its parameters before writing code*. The colleague analyzed intent detection scoring, signal normalization, regression-based fine-tuning, and flow diagrams — before touching implementation.

---

## 6. Presentation Artifacts

| File | Description |
|------|-------------|
| `presentations/lead-brief-finetuning/index.html` | V1 — original Reveal.js presentation |
| `presentations/lead-brief-finetuning/v2-grounded.html` | V2 — grounded version with verified sources, softened claims, actual domain signals |

**Tech stack:** Single-file HTML, Reveal.js 5.0.4 (CDN), Mermaid.js (CDN), CSS variables for AmEx theme. No build step — open in browser.

---

## 7. What's Happening Next

### New Work Streams

1. **Prompt creation** — helping craft and iterate on prompts for the lead brief task
2. **Pitch preparation** — working with Business Analyst to prepare a pitch for sales reps about these leads

### Key Questions for the Pitch Phase

**What to collect as inputs:**
- What does the sales rep actually need before a call? (not what's available — what's useful)
- Which signals correlate with successful outcomes? (this is a product decision)
- What does "good lead" actually mean? Is it conversion likelihood? Deal size? Retention?

**How to decide what makes a good pitch:**
- What's the rep's workflow? When do they read this? (10 seconds before a call? Morning planning?)
- What actions should the brief recommend? (upsell specific product? Retain? Cross-sell?)
- What's the baseline? (What do reps have today without the brief?)

**Prompt versioning and management:**
- Version prompts with a naming convention (e.g., `v1.0_basic`, `v1.1_with_intent_signals`)
- Store prompts alongside configs (like YAML recipes in the current pipeline)
- Track prompt → output quality metrics per version
- Consider: system prompt (fixed persona/format rules) vs. user prompt (per-lead JSON + instruction)
- If prompts grow beyond ~1500 tokens and volume is high → that's when fine-tuning becomes the better path (we've already proven this works)

### The Prompt vs Fine-tuning Decision Matrix

| Situation | Use Prompt Engineering | Use Fine-tuning |
|-----------|----------------------|-----------------|
| Format still changing | ✅ Iterate fast | ❌ Too early |
| Format locked, high volume | ❌ Expensive per call | ✅ Short prompts, more throughput |
| Need sales rep feedback loop | ✅ Easy to adjust | ❌ Retrain cycle |
| Consistency critical | ⚠️ Prompt can drift | ✅ Format in weights |
| Multiple use cases | ✅ Different prompts | ✅ Different LoRA adapters |

---

## 8. How to Use This Document in a New Session

Paste or reference this file at session start and say something like:

> *"I'm continuing work on the AmEx lead brief project. Read `notes/session_state_transfer.md` for full context. We previously built a fine-tuning POC and presented it. Now I'm working on [prompt creation / pitch prep / evaluation / etc.]."*

The key artifacts to point to:
- This file for context
- `presentations/lead-brief-finetuning/v2-grounded.html` for what was presented
- `src/config.py` + `scripts/train.py` for how the pipeline works
- `notes/reproduction_spec.md` for full pipeline reproduction steps
