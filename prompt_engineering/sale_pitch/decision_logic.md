# Decision Logic — Lead-to-Card Matching

## Overview

This documents the decision tree for matching a CRM lead to the best-fit AMEX card product. The logic flows: **Raw Lead Data → Derived Signals → Program Type → Card Selection**.

---

## Step 1: Input Data (from CRM)

| Field | Type | Example |
|---|---|---|
| Cards Held | list | ["Visa Business", "Chase Ink"] |
| Spend Categories | list + amounts | {"advertising": 25000, "shipping": 15000, ...} |
| Annual Spend | number | $960,000 |
| Annual Revenue | number | $6,000,000 |
| Intent Signals | list | ["responded to offer", "visited pricing page"] |
| Company Size (employees) | number | 45 |
| Industry | string | "Construction" |
| Current Payment Methods | dict | {"checks": 40%, "debit": 30%, "credit_card": 30%} |

---

## Step 2: Derive Opportunity Signals

From raw data, compute these signals:

| Signal | How to Derive | Values |
|---|---|---|
| **Travel Intensity** | travel-category spend / total spend; presence of airline/hotel merchants | High / Moderate / Low |
| **Hotel Loyalty** | hotel-specific spend, frequency of hotel transactions | Yes / No |
| **Vendor Spend Concentration** | top-3 categories as % of total; category count | Concentrated / Dispersed |
| **High Total Spend** | annual spend > threshold (e.g. $500K) | Yes / No |
| **Large Purchase Frequency** | count of transactions ≥ $5,000 | High / Moderate / Low |
| **Employee Spend Distribution** | # employees who make purchases | Individual / Multi-employee |
| **Current Card Gap** | no AMEX card held, or holding lower-tier | Upgrade / New / Cross-sell |

---

## Step 3: Program Type Split

**Decision: Business Cards vs Corporate Cards**

```
IF company_size <= ~10 employees
   AND billing = individual owner / personal guarantee
   AND spend = primarily owner-driven
→ BUSINESS CARDS

IF company_size > ~10 employees
   OR needs central billing / admin controls
   OR multiple employees travel on company behalf
→ CORPORATE CARDS
```

> This is the first and most important fork. Revenue alone doesn't determine this — a $4M company with 3 employees goes Business; a $4M company with 50 employees goes Corporate.

---

## Step 4a: Business Card Selection

```
IF travel_intensity = High
   AND high_total_spend = Yes
→ BUSINESS PLATINUM ($895)
   Rationale: Premium travel benefits, lounge access, airline credits justify the fee

IF vendor_spend_concentration = Concentrated
   AND top categories OVERLAP Business Gold eligible categories
   (ads, electronics/software, restaurants, gas, transit, wireless)
→ BUSINESS GOLD ($375)
   Rationale: 4x on auto-selected top 2 categories = maximum points yield

IF general_spend pattern
   AND low complexity
   AND small team
→ BUSINESS GREEN ($95)
   Rationale: Low fee, broad MR earning, simple expense management
```

### Business Gold — Category Match Rules

The Gold card auto-selects the top 2 of these 6 categories per billing cycle:
1. Media/advertising (online, TV, radio)
2. Electronics, software & cloud
3. Restaurants (incl. takeout/delivery)
4. Gas stations
5. Transit (trains, rideshare, tolls, parking, buses, subways)
6. Wireless telephone

**If ≥2 of the lead's top spend categories hit this list → strong Business Gold signal.**

---

## Step 4b: Corporate Card Selection

```
IF travel_intensity = High (frequent exec travel)
   AND high_total_spend = Yes
→ CORPORATE PLATINUM ($550)
   Rationale: Premium exec travel, 5% cashback on employee cards, lounge access

IF travel_intensity = Moderate
   AND entertainment_spend present
→ CORPORATE GOLD ($250)
   Rationale: Travel + entertainment balance

IF basic_travel OR general_employee_expenses
→ CORPORATE GREEN ($75)
   Rationale: Day-to-day employee spending, low fee

IF meeting_event_spend is significant
→ CORPORATE MEETING CARD ($75)
   Rationale: Specialized for meeting/event transactions

IF procurement_heavy
   AND needs employee purchasing cards
→ CORPORATE PURCHASE CARD ($0)
   Rationale: No fee, procurement-focused, employee card controls
```

---

## Step 5: Multi-Card Opportunities

A single lead may warrant **multiple card recommendations**:
- **Primary**: The best-fit card for the lead's dominant signal
- **Secondary**: Complementary cards for other needs

Example: A 50-person construction firm with exec travel + procurement needs:
- Primary: Corporate Platinum (exec travel)
- Secondary: Corporate Purchase Card (procurement for field employees)

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Borderline company size (8-15 employees) | Present both Business + Corporate options; let pitch note the choice |
| Already holds AMEX card | Frame as upgrade/cross-sell, not new acquisition |
| No clear signal concentration | Default to Green (Business or Corporate based on program type) |
| Multiple strong signals | Lead with strongest signal, mention secondary in pitch |
