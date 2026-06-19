# VOC To Product Definition Workflow

This guide shows how a product manager or Amazon seller can turn Review Analyzer output into product definition work.

The goal is not to treat review analysis as a final launch decision. The goal is to convert customer language into better hypotheses, clearer listing changes, and a focused validation plan.

## When To Use This Workflow

Use this workflow after running one of these tools:

- `voc_full`
- `analyze_reviews`
- `analyze_csv`
- `extract_listing_improvements`
- `render_dashboard`

It is most useful when you are evaluating:

- A new Amazon product idea.
- A competitor ASIN.
- A weak listing with conversion or rating problems.
- A product refresh or version-2 improvement.
- A non-Amazon review export from Shopify, eBay, or another channel.

## 1. Separate Facts From Interpretation

Start by keeping raw evidence separate from the product manager's reading.

| Layer | Example |
| --- | --- |
| Fact | 18 reviews mention the lid cracking after repeated use |
| Interpretation | Durability may be a purchase-risk driver |
| Product hypothesis | Reinforce hinge/lid structure and show durability proof in images |
| Validation needed | Sample stress test and packaging drop test |

Avoid jumping directly from one complaint to a final product change. Look for repeated patterns.

## 2. Convert Review Themes Into JTBD

For each high-frequency theme, translate it into a job-to-be-done statement.

| Review Theme | JTBD Statement | Product Implication |
| --- | --- | --- |
| Hard to clean | When I use this every day, I want cleanup to be quick so it does not become another chore | Material, surface, and disassembly matter |
| Does not fit | When I buy this for a specific space or accessory, I need confidence it will fit before ordering | Size chart, compatibility table, and visual proof matter |
| Looks cheap | When this sits in my kitchen/home/office, I want it to match the space | Finish, material, color, and lifestyle images matter |
| Arrived damaged | When I order online, I expect the product to survive shipping | Packaging, corner protection, and inspection matter |

## 3. Prioritize Pain Points

Not every complaint deserves a product change. Score each pain point before acting.

| Dimension | Question |
| --- | --- |
| Frequency | Does this appear repeatedly across reviews or only once? |
| Severity | Does it cause returns, bad ratings, safety concern, or just mild annoyance? |
| Differentiation | Would fixing it create a visible reason to choose this product? |
| Feasibility | Can the seller fix it without destroying cost, timeline, or compliance? |
| Proof | Can the listing prove the fix with images, video, data, or packaging claims? |

Recommended priority labels:

- `P0`: Frequent, severe, and likely to hurt conversion/returns.
- `P1`: Meaningful but needs more evidence.
- `P2`: Nice-to-have, cosmetic, or low-frequency.

## 4. Build A Product Definition Hypothesis

Use this structure after VOC analysis:

```text
Target customer:
Primary use scenario:
Main customer job:
Top P0 pain point:
Product change hypothesis:
Listing proof required:
Sample validation required:
Risk if wrong:
```

Example:

```text
Target customer: Small-apartment coffee drinker
Primary use scenario: Keeping capsules organized on a narrow counter
Main customer job: Store capsules without losing counter space
Top P0 pain point: Bulky holders take too much space
Product change hypothesis: Compact vertical footprint with stable base
Listing proof required: Countertop size comparison image
Sample validation required: Stability test with full load
Risk if wrong: Product looks different but does not solve the space problem
```

## 5. Turn VOC Into Listing Improvements

Review Analyzer can produce listing suggestions. Product managers should connect each suggestion to evidence.

| Listing Area | VOC Input | Improvement |
| --- | --- | --- |
| Title | Repeated search/use wording | Include the clearest use case, not every keyword |
| Bullets | Common buying concerns | Answer fit, material, size, cleaning, durability, or setup questions |
| Images | Confusion or expectation mismatch | Add comparison, dimensions, steps, and proof images |
| A+ Content | Repeated objections | Explain why the product is different and how it solves the objection |
| FAQ/Q&A | Recurring pre-purchase doubts | Turn review confusion into buyer-facing answers |

Do not claim fixes that have not been validated by the product, packaging, or supplier.

## 6. Create A Validation Plan

Before changing tooling, ordering inventory, or scaling ads, turn VOC into tests.

| Test | Purpose |
| --- | --- |
| Sample stress test | Validate durability claims |
| Fit/compatibility test | Validate size or accessory compatibility |
| Cleaning/use test | Validate repeated-use experience |
| Packaging drop test | Validate damage prevention |
| Image comprehension test | Validate whether buyers understand size and use case |
| Competitor comparison | Validate whether the difference is visible enough |

## 7. Decision Output

A useful VOC-to-product-definition memo should end with:

```text
## Summary
## Evidence Used
## Top Customer Jobs
## P0/P1/P2 Pain Points
## Product Definition Hypotheses
## Listing Improvements
## Validation Plan
## Risks
## Open Questions
```

## Anti-Patterns

- Treating a single review as a product truth.
- Rewriting a listing without fixing the product issue.
- Adding features that increase cost but do not address a repeated pain.
- Claiming compliance, safety, or patent clearance from review data alone.
- Moving to supplier commitment before sample validation.

## Practical Agent Prompt

```text
Use the VOC report below to create a product-definition memo.

Separate facts from interpretation.
Rank pain points as P0/P1/P2.
Convert repeated themes into JTBD statements.
Suggest product-definition hypotheses and listing improvements.
List validation tests needed before sourcing or scaling.
Do not invent review frequency, sales, compliance, patent, or ROI conclusions.

VOC report:
```
