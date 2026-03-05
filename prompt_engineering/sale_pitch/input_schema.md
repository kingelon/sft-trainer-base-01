# Input Schema — Lead Data Fields

## CRM Data Row (what the system receives per lead)

### Required Fields
These must be present for pitch generation. If missing, flag for manual review.

| Field | Type | Description | Example |
|---|---|---|---|
| `company_name` | string | Legal or DBA name | "Apex Construction LLC" |
| `industry` | string | Industry / SIC classification | "Construction" |
| `annual_revenue` | number | Annual revenue in USD | 6000000 |
| `company_size` | number | Number of employees | 45 |

### Expected Fields
These significantly improve pitch quality. The prompt handles them gracefully if missing.

| Field | Type | Description | Example |
|---|---|---|---|
| `annual_spend` | number | Total annual business spend | 960000 |
| `monthly_expenses` | number | Estimated monthly operating expenses | 80000 |
| `top_spend_categories` | list[dict] | Top spending categories with amounts | [{"category": "construction_materials", "annual_amount": 300000}, ...] |
| `current_payment_methods` | dict | How they currently pay (% breakdown) | {"checks": 40, "debit": 30, "credit_card": 30} |
| `cards_held` | list[string] | Existing credit/charge cards | ["Chase Ink Business", "Capital One Spark"] |

### Optional / Enrichment Fields
These add specificity to the pitch when available.

| Field | Type | Description | Example |
|---|---|---|---|
| `contact_name` | string | Primary contact / decision maker | "Sarah Chen" |
| `contact_title` | string | Title | "CFO" |
| `city_state` | string | Location | "Dallas, TX" |
| `travel_spend` | number | Annual travel-related spend | 45000 |
| `large_purchase_count` | number | # of transactions ≥ $5K per year | 24 |
| `intent_signals` | list[string] | Behavioral signals | ["visited amex.com", "responded to direct mail"] |
| `existing_amex_relationship` | boolean | Has any AMEX product | false |

---

## Derived Signals (computed before prompt, fed as context)

These are calculated from the CRM fields and passed into the prompt alongside the raw data:

| Signal | Derivation | Passed As |
|---|---|---|
| `program_type` | company_size + billing structure → "Business" or "Corporate" | string |
| `recommended_card` | Decision logic applied to signals (see `decision_logic.md`) | string |
| `travel_intensity` | travel_spend / annual_spend; merchant categories | "High" / "Moderate" / "Low" |
| `category_concentration` | top-3 categories as % of total spend | "Concentrated" / "Dispersed" |
| `payment_method_opportunity` | % currently on checks/debit/ACH (non-card) | percentage |
| `large_purchase_signal` | large_purchase_count > threshold | boolean |
| `card_gap` | no AMEX held, or opportunity for upgrade | "New" / "Upgrade" / "Cross-sell" |

---

## How the Prompt Receives Input

The system prompt expects a structured block injected at call time:

```
### LEAD DATA
- Company: {company_name}
- Industry: {industry}
- Annual Revenue: ${annual_revenue}
- Employees: {company_size}
- Annual Spend: ${annual_spend}
- Monthly Expenses: ${monthly_expenses}
- Top Spend Categories: {formatted_categories}
- Current Payment: {formatted_payment_methods}
- Cards Held: {cards_held}
- Travel Spend: ${travel_spend}
- Large Purchases (≥$5K/yr): {large_purchase_count}

### DERIVED SIGNALS
- Program Type: {program_type}
- Recommended Card: {recommended_card}
- Travel Intensity: {travel_intensity}
- Category Concentration: {category_concentration}
- Non-Card Payment %: {payment_method_opportunity}%
- Card Gap: {card_gap}
```

Missing fields should be passed as "Not available" — the prompt handles graceful degradation.
