# Production Truth Layer

This directory is an additive production adapter. It does not duplicate or override the SwitchBot Product Knowledge Hub.

Source order:

1. Product Knowledge canonical records and runtime index.
2. Current SwitchBot Japan official product / legal pages.
3. Recovered Tier A SwitchBot EDM footer evidence.
4. Campaign-specific human input.

Every field keeps an explicit state: `VERIFIED`, `APPROVED`, `UNVERIFIED`, `MISSING`, or `NOT_REQUIRED`. `VERIFIED` means the source was confirmed; it does not automatically grant approval for external reuse. Product or campaign content is production-eligible only when the relevant approval scope is also satisfied.

The two Phase 6 pilots remain fail-closed because Product Knowledge currently exposes no Approved External Claim for either product and the ESP preference / unsubscribe URLs are unresolved runtime values.

