# PDF Product Matrix Extraction Prompt

> **Purpose:** Use this prompt with a long-context LLM (like GPT-4o, Claude 3.5 Sonnet, or Gemini 1.5 Pro) by attaching the 5 PDF fact sheets. It will extract the exact structured data we need to unblock the Pitch product recommendation logic.

---

**Copy and paste everything below this line into your LLM along with the 5 PDFs:**

---

**ROLE**
You are an expert commercial card product analyst. I have attached 5 fact sheets for AMEX Business and Corporate cards. 

**OBJECTIVE**
Extract a structured product benefits matrix from these documents. I do not want a summary. I need highly specific, structured extraction that answers three distinct business needs.

**OUTPUT FORMAT**
Provide the output in 3 distinct Markdown sections as defined below.

### Section 1: The Core Benefit Matrix
Create a table with the following cards as rows: [Business Gold, Business Platinum, Corporate Gold, Corporate Platinum, Corporate Green (if present)].

For each card, extract these exact columns:
1. **Annual Fee**
2. **Core Earning Mechanic:** Extract the specific points multiplier and the exact categories it applies to (e.g., "4x on top 2 categories: gas, restaurants, shipping..."). List the categories explicitly.
3. **Travel Perks:** Specific statement credits (e.g., "$200 airline fee"), lounge access types, and elite status granted.
4. **Business/Corporate Controls:** Does it have centralized billing? Company liability vs Personal guarantee? Employee card fee structures?

### Section 2: Direct Card Comparisons (The "Why Switch" Bridges)
I need to know exactly how to pitch an upgrade or cross-system switch. Based *only* on the attached documents, provide bulleted lists comparing the following pairs. For each pair, explicitly state (1) what the upgrade gives that the baseline lacks, and (2) what type of spend profile warrants the switch.

- Pair A: Business Gold vs. Business Platinum
- Pair B: Corporate Gold vs. Corporate Platinum
- Pair C: Business Platinum vs. Corporate Platinum (The $4M–$10M revenue crossing line)

### Section 3: The Propensity Routing Gap
We need to map companies with $4M–$10M in revenue to specific corporate cards based on their "Corporate Propensity". 
Based on the positioning, ideal customer profiles, or feature sets described in the documents, extract any language that indicates *which type of business profile* fits:
- Corporate Platinum (What specific scale, travel volume, or need justifies this?)
- Corporate Gold (What defines the "moderate" corporate user?)
- Business Cards (When does a mid-market company still belong on a Business product over a Corporate product?)

**RULES**
- Do not hallucinate or pull in outside knowledge about AMEX cards. If a specific fee or multiplier is NOT in the text of the attached PDFs, explicitly write "Not specified in documents."
- Be extremely precise with reward caps (e.g., "up to $150,000 in combined purchases") and merchant definitions.
