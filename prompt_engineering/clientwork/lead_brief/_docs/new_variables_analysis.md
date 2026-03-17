# New Variables Analysis — Spend Predictions & NRR

> **Purpose:** Analyze the 5 new columns being introduced, document what we know vs. don't know, and frame precise questions to unblock prompt integration.
> **Date:** 2026-03-12

---

## 1. What We Received

Three new variable groups from model-scored tables:

### Prospect Spend Predictions
> Source: `cpdb2_202602_us_spend_tele_field_v1_3_scores_iv`

| Column | Inferred Meaning | Sample Values |
|---|---|---|
| `prosp_pred_tele_bgr` | Predicted spend on **Business Green** for a prospect | 20499.77, 7832.50 |
| `prosp_pred_tele_bplat` | Predicted spend on **Business Platinum** for a prospect | 25407.83, 13228.87 |

### Customer Spend Predictions
> Source: `cpdb2_us_cust_spend_dm_tele_field_v1_3_scores_iv`

| Column | Inferred Meaning | Sample Values |
|---|---|---|
| `cust_pred_tele_bgr` | Predicted spend on **Business Green** for an existing customer | 2891.22, 3015.22 |
| `cust_pred_tele_bplat` | Predicted spend on **Business Platinum** for an existing customer | 5928.49, 6052.49 |

### NRR (Net Retention Rate)
> Source: `us_sales_nrr_v1_8_fresh_leads_scores_iv`

| Column | Inferred Meaning | Sample Values |
|---|---|---|
| `pred_tele_fresh` | Predicted Net Retention Rate for fresh tele-leads | 0.007006, 0.004045, 0.040607 |

---

## 2. What We Know

From sample data patterns and naming conventions:

- **`prosp_` vs `cust_`** — a prospect/customer split exists. Prospects are new acquisition; customers are existing AMEX cardholders.
- **`bgr` and `bplat`** — predictions are card-specific: Business Green and Business Platinum. These are the two card tiers being scored.
- **`pred_tele_`** — the "pred" prefix signals these are model outputs (predictions), and "tele" likely means the tele-sales channel.
- **Values are numeric, continuous** — not buckets. Spend predictions are in dollar amounts (thousands range), NRR is a small decimal (likely a rate or probability).

---

## 3. Layers of Ambiguity

This is where the challenges stack up. Each layer depends on the one before it.

### Layer 1 — What do the numbers represent?

| Question | Why it matters |
|---|---|
| Are spend predictions **monthly** or **annual**? | A $20K predicted monthly spend vs. annual spend tells a completely different story. The prompt needs to frame it correctly. |
| Is spend in **dollars** or some transformed/normalized unit? | The values look like dollar amounts, but we can't assume — they could be log-transformed or scaled. |
| What does NRR = 0.007 mean? | Is it a rate (0.7%)? A probability? A score? Without knowing the unit, we can't say "high" or "low." |
| Is NRR about **retention of the lead** or **retention of revenue** from the lead? | "Net retention rate" in SaaS means revenue retention. Here it could mean the likelihood the lead retains as a customer after acquisition. |

### Layer 2 — How does it relate to the lead?

| Question | Why it matters |
|---|---|
| Is `prosp_pred_tele_bgr` the predicted spend **if they get a Business Green card**? | Or is it their predicted total business spend that would *qualify* them for Business Green? These are different things. |
| Why are there **two card columns** (bgr + bplat) per lead? | Is the higher one the recommendation? Do we pick the card with higher predicted spend? Or are they independent scores? |
| What does it mean when prospect spend is high but customer spend is low (or vice versa)? | Does cust_pred apply only to existing AMEX customers? Is it always null for new prospects? |
| Will **every lead** have all 5 columns populated? | If fill rates are low, we need graceful handling. If some leads only have cust_ and not prosp_, what does that mean? |

### Layer 3 — How do we interpret for the prompt?

| Question | Why it matters |
|---|---|
| What's a "good" predicted spend? Is $25K high or low? | Without distribution data or thresholds, we can't write "strong predicted spend" vs. "moderate." We need **buckets or benchmarks**. |
| Does the Green vs. Platinum split imply a card recommendation? | If `prosp_pred_tele_bplat` >> `prosp_pred_tele_bgr`, does that mean "recommend Platinum"? Or is that handled by the existing propensity model separately? |
| How does this interact with the existing `corp_propensity` signal? | The current prompt already has a propensity-based card selection. These new variables could conflict or complement. |
| What should NRR drive in the "why good lead" text? | Should high NRR → "likely to retain, safe investment"? Should low NRR → don't mention? What's the threshold? |

### Layer 4 — How do we word it?

| Challenge | Example |
|---|---|
| We can't say "predicted to spend $25K on Business Platinum" if we don't know it's annual, in dollars, on that card | The rep reads it → takes it literally → says it on the call → wrong |
| We can't bucket without knowing the distribution | Calling $7K "moderate" when 90% of leads are under $5K would undersell it |
| Prospect vs. Customer distinction is confusing in natural language | "Predicted prospect spend of $20K" — a rep might ask "prospect of what?" |
| NRR as a small decimal reads as noise to a non-technical reader | 0.004 means nothing without framing |

---

## 4. What We Need to Ask — Structured Questions

### A. Variable Definitions

1. **What unit are the spend predictions in?** Dollars? Monthly? Annual? Normalized?
2. **What does the prediction represent?** Predicted spend *on that card product* if acquired? Or predicted business spend that *maps to* that card tier?
3. **What does NRR (`pred_tele_fresh`) represent?** Net retention rate of what — revenue, the lead as a customer, the card relationship? What's the unit — probability, rate, score?
4. **Is `pred_tele_fresh` bounded?** (e.g., 0 to 1, or unbounded?) What is the typical range in practice?

### B. Data Coverage & Structure

5. **Fill rates:** What % of leads have each of these 5 columns populated? Are there leads with only cust_ or only prosp_ values?
6. **Prospect vs Customer:** Is this a mutually exclusive flag? (i.e., a lead is either a prospect OR a customer, not both?) Or can a lead have both prosp_ and cust_ values?
7. **Will these columns be available for every lead that hits the prompt?** Or only for specific segments (e.g., tele-sales channel only)?

### C. Interpretation & Thresholds

8. **Can we get the distribution summary?** (p25, p50, p75, max) for each of the 5 columns — so we can define "High / Medium / Low" buckets.
9. **Is the higher of bgr vs bplat intended as the card recommendation?** Or is card selection still driven by the existing propensity model, and these spend values are supplementary context?
10. **What's a meaningful NRR threshold?** At what value should we consider a lead to have "strong" retention signal? Is there a cutoff below which it's noise?

### D. Integration with Existing Signals

11. **How do these variables interact with `corp_propensity`?** Are they replacing it, supplementing it, or independent?
12. **Should predicted spend influence card selection or just support the "why good lead" narrative?** (e.g., "high predicted platinum spend" → recommend Platinum, or is that already handled upstream?)

---

## 5. Proposed Prompt Integration (Once Questions Are Answered)

> This is a preview of how we'd incorporate. We can't finalize until questions above are answered.

### New Signal Category in "What to Include"

After Hot Signals, add a third priority block:

```
### Predicted Spend & Retention Signals (if present)

- If predicted spend values are present, summarize the strongest signal
- Frame as forward-looking opportunity: "Predicted annual spend of ~$[X]K on [Card]"
- If NRR is above [threshold], mention retention strength
- If both prospect and customer spend are present, lead with the higher-value signal
```

### New Line in Output

A sentence like:
> "Predicted spend modeling indicates approximately ~$25K in potential Business Platinum spend, with a [strong/favorable] retention outlook."

But we **cannot write this line** until we know:
- What the numbers actually represent
- What "good" looks like (thresholds)
- How to frame prospect vs customer distinction

---

## 6. Summary — The Ask in One Sentence

> We have 5 new model-scored variables (2 prospect spend, 2 customer spend, 1 NRR) and need **definitions, units, distributions, and interpretation guidance** before we can responsibly incorporate them into the "why good lead" prompt output.
