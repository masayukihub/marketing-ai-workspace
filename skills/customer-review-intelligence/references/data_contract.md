# Data contract

## Identity and provenance

Every normalized record must retain `review_id`, `version_id`, `source`, `source_review_id`, `source_id`, `source_url`, `channel_product_url`, `raw_file_path`, `collected_at`, `last_checked_at`, `original_review_hash`, and `batch_id`.

Resolve product identity into:

- `product_id`: canonical Product Knowledge product.
- `variant_id`: color, size, generation, or format when verified.
- `bundle_id`: bundle identity when verified.
- `mapping_status`: `Confirmed`, `Probable`, `Unmapped`, or `Conflicting`.
- `mapping_basis`: identifier or exact alias used.

Only `Confirmed` records enter formal product totals. Keep other records visible in data-quality and manual-review outputs.

## Evidence type

- `record_type`: canonical values are `ec_review`, `sns_post`, `comment`, `kol_content`, `media_article`, `official_post`, `pr_content`, or `imported_record`. Preserve an adapter's original value in `source_record_type`; map `video_comment` to `comment`, `social_post` to `sns_post`, `official_content` to `official_post`, and `media_content` to `media_article` at export boundaries.
- `relationship_type`: `organic`, `paid_kol`, `paid_or_affiliate`, `pr_placement`, `syndicated`, `official`, `owned`, or `unknown`.
- `voc_eligibility`: `Natural VOC`, `Context Only`, `Non-VOC`, or `Unverified`.

Official, paid, and syndicated content is never Natural VOC. User comments below such content may be Natural VOC when the product and user opinion are explicit.

## State and coverage

- `review_status`: `Active`, `Updated`, `Deleted`, or `Incomplete`.
- `coverage_status`: `Complete`, `Zero Confirmed`, `Partial`, `Blocked`, or `Not Configured`.
- Preserve all versions in `review_versions.csv`.
- Never infer deletion from a partial or blocked collection.

## Classification

Keep `rating`, `sentiment`, `sentiment_score`, `primary_topic`, `secondary_topics`, `issue_category`, `issue_subcategory`, `severity`, `analysis_confidence`, `classification_basis`, and `manual_review_required`.

Use `Yes`, `No`, or `Unknown` for evidence-dependent flags. Missing is not `No`.
