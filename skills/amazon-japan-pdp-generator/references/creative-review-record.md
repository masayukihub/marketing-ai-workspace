# Record a review of the exported image

Open the exact candidate at full size and the intended mobile display width. Record what is visible, where the problem is, which parts to preserve and the smallest useful correction. File checks, metadata scores and a prompt are not an image review.

The legacy input accepts `images[].creativeReview` and `aplusModules[].creativeReview`. V4 accepts `creative_reviews.desktop` / `creative_reviews.mobile` on the gallery/module record. Desktop and mobile files have independent hashes.

Start with this incomplete record and fill it only after inspection:

```json
{
  "asset_id": "CURRENT_ASSET_ID",
  "output_ref": "design/product_images/image_02.jpg",
  "output_sha256": null,
  "reviewer": {"kind": "model", "name": null},
  "inspected_at": null,
  "viewing_context": null,
  "five_second_takeaway": null,
  "findings": {
    "message_clarity": {"verdict": "UNASSESSED", "observation": null},
    "product_fidelity": {"verdict": "UNASSESSED", "observation": null},
    "visual_proof": {"verdict": "UNASSESSED", "observation": null},
    "composition": {"verdict": "UNASSESSED", "observation": null},
    "realism": {"verdict": "UNASSESSED", "observation": null},
    "brand_fit": {"verdict": "UNASSESSED", "observation": null},
    "mobile_readability": {"verdict": "UNASSESSED", "observation": null}
  }
}
```

Use `sha256sum <actual-file>` for the hash and a real ISO inspection timestamp. `viewing_context` describes the actual views, such as original export, thumbnail and 390px display. Record the observed takeaway; do not auto-copy the headline.

Each finding needs `PASS`, `REVISE`, `BLOCKED` or a justified `NOT_APPLICABLE`, plus a specific observation. Message, identity, composition and mobile reading cannot be skipped. Use the outer project/asset ledger for any correction plan and candidate selection.

After recording observations in the source input/Spec, rerun the existing production command for the authorized scope. The legacy renderer computes the new output hash and checks the record. It returns `Need Verification` until the exact file has a complete passing review; changed pixels, filename or asset ID invalidate it. The V4 manifest records desktop/mobile review status alongside source and file evidence. Neither path edits human approval.

`evaluateCreativeReview` validates the record and its binding, **not the truth of the reviewer’s observations**. It cannot prove a human/model actually looked at pixels, and it does not call a vision model. Never fabricate findings to satisfy the schema. Existing human selection, whole-set review, Claim, source, mobile/browser and publication requirements remain in force.

Old `round2Qa` now means content/layout metadata only; use `creativeReviewResult` for image observations. Old report consumers must display null scores as unassessed. Existing output paths are retained for compatibility and may contain unreviewed candidates.
