# Business application rules

Use these rules when translating normalized VOC into product, marketing, EC, PR/KOL, support, or management outputs.

## Evidence chain

Every recommendation must retain `review_id`, source, URL, sample size, date window, coverage status, confidence, and one to three relevant source-language quotations. The quote must come from a review actually linked to the recommendation. If no relevant quotation exists, label it `Evidence Insufficient`; never substitute an AI summary. Label root causes as `[Hypothesis]` until validated with product telemetry, return reasons, support tickets, or engineering reproduction.

## Six-level sentiment

Keep the core sentiment field unchanged. Derive a business sentiment layer:

- `Strong Positive`: positive text with rating 5 and no material complaint.
- `Positive`: positive text or rating 4–5 without strong contradiction.
- `Neutral`: descriptive or unclear text without material polarity.
- `Negative`: negative text or rating 2–3 with a material complaint.
- `Strong Negative`: rating 1–2 with unusable, failure, return, safety, privacy, or severe disappointment evidence.
- `Mixed`: meaningful positive and negative evidence in the same review.

Always flag rating/text conflicts. A high rating does not erase a complaint.

## Issue priority

Score issue clusters on a 0–100 scale with visible components:

`Priority = 25% frequency + 20% negative intensity + 15% rating impact + 10% helpfulness + 15% recency/growth + 15% product importance`.

Normalize each component to 0–100 within the analyzed product and window. If helpful votes or comparable history are unavailable, mark those components `Not Available`, redistribute no weight, and lower confidence rather than inventing values.

- P0: safety, privacy, compliance, property loss, or credible systemic core failure.
- P1: score ≥70, or repeated high-severity evidence affecting core use/return/recommendation.
- P2: score 40–69 with repeated evidence.
- P3: score <40 with more than one credible record.
- Monitor: one record, low confidence, or incomplete attribution.

## Business routing

- Product/Engineering: reproducible hardware, software, firmware, UX, compatibility, or design issues.
- Marketing/EC: proven value propositions, purchase motivations, expectation gaps, FAQ needs, and claim corrections.
- Support/Content: setup questions, discoverability, explainable limitations, troubleshooting, and service handling.
- Logistics: delivery, packaging, or seller-fulfilment issues; never count these as product quality without separate evidence.

## Voice library and quotation safety

Preserve original Japanese text, line breaks, punctuation, emoji, stable `review_id`, and URL. The original text is the evidence source of truth and must not be overwritten by cleaned text, translation, excerpt, or summary. Chinese summaries must preserve meaning and remain separate derived fields. Marketing suitability means internal discovery only unless reuse authorization is confirmed. Never turn anonymous marketplace text into an expert endorsement.

Product Backlog and marketing applications must show the evidence denominator, affected channels, confidence, and linked Japanese quotations. A quote opens the corresponding voice record and, where available, the original source URL.

Issue Center and Voice Library must each include a scoped analysis summary. Use `[Fact]`, `[Insight]`, `[Hypothesis]`, `[Recommendation]`, and `[Data Gap]` labels. The summary must state the active sample scope and denominator and must update with supported filters.

## Dashboard

Default to an offline, read-only HTML dashboard backed by reviewed local data. Show the date window, source coverage, sample size, denominator, and Partial/Blocked status. Filters must update all relevant cards, charts, and detail rows. Do not use a word cloud as the core analysis.

A word cloud is optional as a secondary discovery tool when the user requests it. Build it from filtered original Japanese text, not summaries. Remove auditable stopwords, brand/product names, URLs, emoji, particles, and meaningless single characters; prefer interpretable nouns, adjectives, and short phrases. Count distinct `review_id`, cap at 30 terms, expose the numerator/denominator/channel count/sentiment mix, and allow a term click to filter the underlying voices. Keep Natural VOC separate from PR, KOL, media, and official content.
