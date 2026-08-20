# Analysis rules

## Evidence labels

- `[Fact]`: directly supported by collected records.
- `[Insight]`: synthesis supported by multiple comparable records.
- `[Hypothesis]`: plausible explanation requiring validation.
- `[Recommendation]`: proposed action.
- `[Data Gap]`: missing or incomparable evidence.
- `[Risk]`: safety, privacy, compliance, access, or decision risk.

## Sentiment and severity

Use rating as context, not the classifier. Handle negation and contrast such as `接続できないと思ったが、設定をやり直したら使えた`. Five-star complaints and three-star pros/cons can be `Mixed`.

Escalate Critical for safety, privacy, fire/heat, lockout, property loss, compliance, or credible systemic failure. Escalate High for unusable core functions, rapid failure, repeated replacement, explicit return/refund, or concentrated recurrence.

## Responsibility

Assign one primary responsibility:

- Product, Hardware, Firmware, App, Customer Support, Logistics, Marketing, EC, or Quality Assurance.

Distinguish:

- information absent;
- information present but hard to find;
- user did not read;
- user read but could not understand;
- real product experience issue;
- compatibility limitation;
- individual preference.

Create a TODO only for repeated/multi-source issues, core-use or safety risks, confirmed information gaps, low-cost FAQ/content fixes, or credible product investigation needs.

## Trend

Require at least three comparable periods for a sustained trend. Compare equal windows and disclose source coverage, sample size, product version, firmware, promotion, and channel mix. Do not interpret channel audience differences as product differences.

