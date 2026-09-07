// Validates recorded observations, never judges image pixels or grants approval.
export const CREATIVE_DIMENSIONS = Object.freeze([
  "message_clarity", "product_fidelity", "visual_proof", "composition",
  "realism", "brand_fit", "mobile_readability",
]);

const nonempty = (value) => typeof value === "string" && value.trim().length > 0;
const hash = (value) => typeof value === "string" && /^[a-f0-9]{64}$/i.test(value);

export function evaluateCreativeReview(review, output) {
  const pending = (reason, stale = false) => ({
    status: "Needs Visual Review", reason, stale,
    scope: "Recorded observations only; human approval and publish gates remain separate.",
    fiveSecondMessage: null,
  });
  if (!review) return pending("Open the exported image and record a creative review.");
  if (!hash(output?.sha256) || review.output_sha256 !== output.sha256 ||
      !nonempty(output?.path) || review.output_ref !== output.path ||
      !nonempty(output?.id) || review.asset_id !== output.id) {
    return pending("Review does not match this exact asset, output path and SHA-256.", true);
  }
  if (!["human", "model"].includes(review.reviewer?.kind) ||
      !nonempty(review.reviewer?.name) || !nonempty(review.inspected_at) ||
      !Number.isFinite(Date.parse(review.inspected_at)) ||
      !nonempty(review.viewing_context) || !nonempty(review.five_second_takeaway)) {
    return pending("Reviewer, inspection time, viewing context and observed takeaway are required.");
  }
  const findings = CREATIVE_DIMENSIONS.map((key) => review.findings?.[key]);
  if (findings.some((finding) => !finding ||
      !["PASS", "REVISE", "BLOCKED", "NOT_APPLICABLE"].includes(finding.verdict) ||
      !nonempty(finding.observation))) {
    return pending("Each creative dimension needs a verdict and a concrete observation.");
  }
  // Identity, composition, message and mobile reading always apply to a listing asset.
  if (["message_clarity", "product_fidelity", "composition", "mobile_readability"]
      .some((key) => review.findings[key].verdict === "NOT_APPLICABLE")) {
    return pending("Core image dimensions cannot be skipped.");
  }
  const rejected = findings.some((finding) => ["REVISE", "BLOCKED"].includes(finding.verdict));
  return {
    status: rejected ? "Reject" : "Pass",
    reason: rejected ? "Resolve the recorded visual defects." : "Observations recorded for this exact output.",
    stale: false,
    scope: "Recorded observations only; human approval and publish gates remain separate.",
    fiveSecondMessage: review.five_second_takeaway,
  };
}
