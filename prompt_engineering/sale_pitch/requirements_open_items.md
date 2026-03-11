# Pitch Prompt — Data Requirements & Open Items

> For client discussion. Outlines what we need to make the pitch engine production-ready.

---

## 1. Card Benefits Dataset

**What we need:** A structured reference of each card's key benefits — rewards mechanics, fees, and differentiators. This becomes the knowledge base the prompt draws from when explaining *why* a card fits.

**What we have today:** A manually-assembled card catalog covering 8 cards (3 Business, 5 Corporate) with fee, rewards, and "best for" summaries.

**What's missing:**

| Gap | Why it matters | Example |
|---|---|---|
| Detailed rewards tiers per card | The pitch needs to cite specific multipliers against the lead's spend categories | "Business Gold earns 4x on restaurants" — we have this. But do we have the full list of merchant codes that qualify? |
| Benefit comparison across cards | When a lead holds Card A, we need to articulate exactly what Card B gives them that A doesn't | "Your Hilton Aspire earns 14x at Hilton properties but 1x on business supplies. The Business Gold earns 4x on your top restaurant spend." |
| Consumer vs. Business card distinctions | Many leads hold personal AMEX cards (Hilton, Blue Cash, etc.) — needed to frame business card separation clearly | What carries over? What doesn't? (e.g., MR earning vs. Hilton points) |

**Ask:** Can we get an official card benefits comparison matrix — ideally structured (not PDF) — covering all AMEX cards a lead might currently hold (including consumer products like Hilton, Blue Cash, Delta)?

---

## 2. Propensity Bucket → Card Recommendation Mapping

**What we need:** A defined mapping from each propensity bucket to a recommended card product, specifically for the **$4M–$10M revenue band** where propensity drives the choice.

**Current state (from Rama's email):**

```
Revenue < $4M    → SBS cards (Business Platinum default)
Revenue $4M–$10M → Apply Corporate Propensity Logic
Revenue > $10M   → Corporate Cards (Corporate Platinum)
BGold            → Catch-all when no clear qualification
```

**Propensity buckets are defined (from the model):**

| Bucket | Corp Propensity Score |
|---|---|
| Very High Corp | 75%+ |
| High Corp | 50–75% |
| Neutral Corp | 25–50% |
| OPEN | <25% |

**What's missing:** The card assignment per bucket. For example:

| Bucket | Suggested Card | Rationale (TBD) |
|---|---|---|
| Very High Corp | Corporate Platinum? Corporate Gold? | Strong corporate signal — but which card? |
| High Corp | Corporate Gold? | Moderate corporate fit |
| Neutral Corp | Business Platinum? | Leans business, but could go either way |
| OPEN | Business Platinum? Business Gold? | Business card territory |

**Ask:** Can we get the mapping finalized? Even a "v0 best guess" we can iterate on would unblock prompt development. The prompt currently accepts the card recommendation as an input — once the mapping exists, it becomes a lookup.

---

## 3. Card Comparison Documents (for RAG)

**Concept:** Pre-generate structured comparison documents for common card pairings. When a lead holds Card X and we're recommending Card Y, the prompt (or RAG layer) retrieves the relevant comparison and uses it to build the "value bridge" in the pitch.

**Why pre-generate vs. in-prompt?**
- Comparisons involve nuance (MR points vs. Hilton points, different category definitions, fee structures) that's hard to get right in free-form generation
- A reviewed, approved comparison doc becomes a controlled source of truth
- RAG can pull the right comparison without stuffing every card's details into the prompt

**Structure per comparison doc:**

```
Comparison: [Current Card] → [Recommended Card]

What they have today:
- [Card name] | $[fee]/yr
- Earns: [rewards mechanic on relevant categories]
- Perks: [key benefits]

What they'd get:
- [Recommended card] | $[fee]/yr  
- Earns: [rewards mechanic — emphasize what hits their spend]
- Perks: [key benefits that differ]

Key differences:
- [Difference 1 — the biggest swing]
- [Difference 2]
- [Difference 3]

Pitch angle:
"[One sentence a rep could say about the switch]"
```

**Example — Hilton Honors Aspire → Business Platinum:**

```
Comparison: Hilton Honors Aspire → Business Platinum

What they have today:
- Hilton Honors Aspire | $550/yr
- Earns: 14x at Hilton properties, 7x on flights/dining, 3x on everything else (Hilton points, not MR)
- Perks: Diamond status, $250 resort credit, Priority Pass lounge access

What they'd get:
- Business Platinum | $895/yr
- Earns: 5x flights/hotels via AmexTravel, 2x on select biz categories + purchases ≥$5K, 1x on everything else (MR points)
- Perks: Global lounge access, airline credits, premium travel, business liability separation

Key differences:
- Currency: Hilton points (hotel-only value) vs. MR points (flights, hotels, transfers, cash)
- Business separation: Aspire is a consumer card — no company expense tracking, no employee cards
- Large purchases: Business Platinum earns 2x on any purchase ≥$5K — Aspire doesn't differentiate

Pitch angle:
"The Aspire is a great personal travel card — keep it for Hilton stays. But your $33K in business supplies should be earning on a business card where those purchases actually count."
```

**Priority comparison pairs to generate:**

| # | Current Card | Recommended Card | When this comes up |
|---|---|---|---|
| 1 | Hilton Honors Aspire | Business Platinum | Leads with consumer Hilton cards, high business spend |
| 2 | Blue Cash (consumer) | Business Gold | Leads with Blue Cash + restaurant/category spend |
| 3 | Hilton + Blue Cash combo | Business Gold | Multiple consumer cards, category alignment |
| 4 | Chase Ink Business | Business Gold | Competitive displacement, category comparison |
| 5 | Visa Corporate | Corporate Platinum | Corporate displacement, upgrade |
| 6 | Business Green (existing) | Business Gold | Same-ecosystem upgrade |
| 7 | No card | Business Green | New acquisition, baseline |
| 8 | No card | Business Platinum | New acquisition, high spend/travel |

**Ask:** Which comparison pairs should we prioritize? Are there cards leads commonly hold that aren't on this list?

---

## 4. Sample Outputs — Simplified Tone

Below are example pitches showing the target tone for each revenue tier. These would be the actual outputs the prompt generates.

### < $4M — Owner-direct, ROI-focused

> **Lead:** Rob Baratheon, funeral services, $1.8M revenue, 3 employees. Spends ~$50K/year across 3 Hilton and 1 Blue Cash consumer cards. Top spend: restaurants.
> **Recommended card:** Business Gold

```
pitch: Rob Baratheon spends about $50K a year across his personal 
AMEX cards — mostly at restaurants — but none of that is earning 
business rewards.

Those Hilton and Blue Cash cards are consumer products. They're not 
tracking business expenses or earning on the categories that matter 
for his funeral services operation.

The Business Gold Card earns 4x on restaurants automatically — 
it picks your top 2 categories each billing cycle, and restaurants 
are Rob's top spend every month.

At $50K annual spend, the $375 fee pays for itself in January, 
and the rest of the year is pure upside.

Rob keeps his Hilton cards for personal travel. The Gold handles 
the business side — clean books, better rewards, one card.

conversation_opener: "Rob, those restaurant charges on your 
account — are those mostly business meals? Because there's an 
easy way to earn 4x on what you're already spending."
```

### $4M–$10M — Propensity-driven, card adapts to signal

> **Lead:** Andy Miller, restaurant president, ~$4M revenue. $32.9K on Hilton Honors Aspire. Top spend: merchandise & supplies. Propensity: OPEN.
> **Recommended card:** Business Platinum

```
pitch: Andy Miller's restaurant does about $4M in revenue and he's 
running $33K in supply purchases through his Hilton Aspire card.

The Aspire earns Hilton points — good for hotel stays, not for 
the kind of steady business spending a restaurant generates 
month after month.

The Business Platinum Card earns 2x on every purchase over $5K 
and gives Andy the travel perks he's used to — lounges, airline 
credits, the full package.

That supply spend starts earning Membership Rewards instead of  
Hilton points, and bigger purchases like equipment or renovations 
automatically hit the 2x tier.

Andy's already an AMEX customer — this isn't a brand switch, 
it's moving business spend onto a card that's built for it.

conversation_opener: "Andy, you're putting your supply orders 
through the Aspire right now — are you getting much back on 
those, or is it mainly a travel card for you?"
```

### > $10M — C-suite, company-wide scale

> **Lead:** Angela Hannigan, C-suite, business services, $17.8M revenue, 55 employees. No AMEX relationship. No current card detail.
> **Recommended card:** Corporate Platinum

```
pitch: Angela Hannigan's firm does nearly $18M with 55 employees — 
and none of that company spending is earning AMEX rewards today.

With a team that size, vendor payments, software, and employee 
travel are probably split across personal cards and bank 
transfers with no centralized view.

The Corporate Platinum Card puts it all under one program — 
company liability, centralized billing, and 5x on flights 
booked through AmexTravel.

Across 55 employees, the 5% cashback on their card spend adds 
up fast — and shifting payments off checks extends cash float 
by 30-55 days per cycle.

No existing AMEX relationship, so this is a clean start — 
one card program, full visibility, rewards from day one.

conversation_opener: "Angela, with 55 people, I'm guessing 
there's a lot of vendor and travel spend happening — is that 
going through a corporate card or more scattered around?"
```

---

## Summary of Open Items

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | Card benefits comparison matrix (structured, all products incl. consumer) | Client / Product team | **Needed** |
| 2 | Propensity bucket → card mapping for $4M–$10M band | Client / Data Science | **Needed** |
| 3 | Priority list of card comparison pairs for pre-generation | Client / Sales team | **Needed** |
| 4 | FRC documents for RAG compliance layer | Client / Governance | In parallel (per Rama's email) |
| 5 | Tone approval on sample outputs above | Client / Leadership | **Ready for review** |
