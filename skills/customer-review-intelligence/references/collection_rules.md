# Collection rules

1. Collect only publicly visible evidence or user-provided files.
2. Do not sign in for the user, type credentials, inspect cookies/storage/passwords, close the user's browser, bypass CAPTCHA, or evade platform controls. If the user explicitly requests their existing external browser, the already-visible authenticated session may be used only through normal UI actions on the requested product/channel pages.
3. Record page number, cutoff, pagination boundary, HTTP result, and failure reason.
4. Continue pagination until the requested window is exhausted or a boundary is explicitly recorded.
5. Save raw HTML/JSON/CSV before normalization. Add SHA-256 to the batch manifest.
6. Preserve source URL and collection time for counts, ratings, engagement, and review text.
7. Mark truncated text `Incomplete`; never reconstruct unseen content.
8. Preserve public display names only in raw/normalized controlled data. Omit them from reports.
9. Do not claim verified purchase unless the page explicitly says so.
10. Treat a successful page with no review objects as `Zero Confirmed` only when the configured review scope and pagination were fully checked; otherwise use `Partial`.

Browser-assisted capture:

- Capture the initial page and every material page/scroll boundary. Save PNG plus visible DOM text/structured records, URL, timestamp, sort mode, visible first/last content ID, first/last visible date, and loaded-count before/after.
- Never rely on screenshots alone for counts. Reconcile extracted unique IDs and preserve the screenshot as visual evidence.
- Stop immediately at CAPTCHA, consent loops, rate-limit warnings, disabled comments, sign-in prompts, or repeated no-progress loads; record the exact boundary and keep `Partial` or `Blocked`.
- Resume from the last confirmed content ID/scroll index; do not restart counts from zero.
- X browser search remains `Partial` because the UI may rank or omit posts and exposes no auditable archive total, even after long scrolling.
- YouTube may be `Complete` only for a fixed, declared video list when comments are sorted as configured, all reply controls are expanded, scrolling reaches the end, displayed counts reconcile, and no load failed. Otherwise use `Partial`.
- Amazon may be `Complete` only for exact mapped ASIN scopes when every accessible review page is traversed and unique review IDs reconcile to the displayed review scope. A shared rating total or login-blocked portal remains `Partial`.

Platform notes:

- Amazon: prefer the exact ASIN review portal with `formatType=current_format`; do not merge shared variants without verified entity mapping.
- Rakuten: check `/1.1/`, `/2.1/`, and later pages until the time window ends.
- Yahoo: inspect the product review page and any pagination or more controls.
- Official store: record the review widget and its pagination boundary.
- X, YouTube, KOL, PR, and media: keep owned/paid/context records separate from natural user comments.
