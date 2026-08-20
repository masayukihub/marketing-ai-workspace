import crypto from "node:crypto";

const MUTATING_OPERATIONS = new Set(["REORDER", "DELETE", "INSERT", "MERGE", "SPLIT"]);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function storySequenceSnapshot(spec) {
  return {
    gallery: (spec.product_images || []).map((item) => ({ id: item.id, sequence: item.sequence, stage: item.stage })),
    aplus: (spec.aplus_modules || []).map((module) => ({
      id: module.id,
      sequence: module.sequence,
      unit_ids: (module.units || []).map((unit) => unit.id),
      unit_stages: (module.units || []).map((unit) => unit.stage),
    })),
  };
}

export function storySequenceFingerprint(spec) {
  return crypto.createHash("sha256").update(JSON.stringify(storySequenceSnapshot(spec))).digest("hex");
}

export function storySequenceLocked(spec) {
  return spec?.story_sequence_lock?.locked === true || spec?.human_gates?.story_approval?.story_sequence_locked === true;
}

export function lockStorySequence(spec, { lockedBy = "Story Gate", lockedOn = new Date().toISOString() } = {}) {
  const fingerprint = storySequenceFingerprint(spec);
  spec.story_sequence_lock = {
    locked: true,
    fingerprint,
    locked_by: lockedBy,
    locked_on: lockedOn,
    allowed_after_lock: ["ANNOTATE", "ADD_DECISION_REASON", "ADD_REFERENCE_TRACE", "MAP_LAYOUT", "ENRICH_METADATA"],
    prohibited_after_lock: [...MUTATING_OPERATIONS],
  };
  spec.human_gates = spec.human_gates || {};
  spec.human_gates.story_approval = spec.human_gates.story_approval || {};
  spec.human_gates.story_approval.story_sequence_locked = true;
  spec.human_gates.story_approval.story_sequence_fingerprint = fingerprint;
  return spec;
}

export function unlockStorySequence(spec, reason = "Story Gate reset for review") {
  spec.story_sequence_lock = {
    locked: false,
    fingerprint: "",
    reset_reason: reason,
    requires_story_review: true,
  };
  if (spec?.human_gates?.story_approval) {
    spec.human_gates.story_approval.story_sequence_locked = false;
    spec.human_gates.story_approval.story_sequence_fingerprint = "";
  }
  return spec;
}

export function assertStoryMutationAllowed(spec, operation) {
  const normalized = String(operation || "").trim().toUpperCase();
  if (storySequenceLocked(spec) && MUTATING_OPERATIONS.has(normalized)) {
    throw new Error(`Story Sequence Lock BLOCKED ${normalized}. Reset Story Gate, return to Story Review, and obtain approval again before changing Gallery/A+ order or units.`);
  }
  return { allowed: true, operation: normalized || "ANNOTATE" };
}

export function assertStorySequenceIntegrity(spec, candidate = spec) {
  if (!storySequenceLocked(spec)) return { pass: true, locked: false };
  const expected = spec.story_sequence_lock?.fingerprint || spec.human_gates?.story_approval?.story_sequence_fingerprint;
  const actual = storySequenceFingerprint(candidate);
  if (!expected || expected !== actual) {
    throw new Error("Story Sequence Lock integrity failure. Story Gate must be reset and re-approved before sequence changes can continue.");
  }
  return { pass: true, locked: true, fingerprint: actual, snapshot: clone(storySequenceSnapshot(candidate)) };
}

export function assertStorySequenceStateIntegrity(spec, state, { allowInitialLock = false } = {}) {
  const stateLocked = state?.story_sequence_locked === true;
  const stateFingerprint = String(state?.story_sequence_fingerprint || "");
  const specLocked = storySequenceLocked(spec);
  const specFingerprint = String(spec?.story_sequence_lock?.fingerprint || spec?.human_gates?.story_approval?.story_sequence_fingerprint || "");
  const actual = storySequenceFingerprint(spec);
  if (stateLocked || stateFingerprint) {
    if (!stateLocked || !stateFingerprint) {
      throw new Error("Story Sequence Lock state is incomplete. Reset Story Gate and return to Story Review before continuing.");
    }
    if (!specLocked || !specFingerprint) {
      throw new Error("Story Sequence Lock was removed from the approved Spec. Reset Story Gate and return to Story Review before continuing.");
    }
    if (stateFingerprint !== specFingerprint || stateFingerprint !== actual) {
      throw new Error("Story Sequence Lock state/spec fingerprint mismatch. Reset Story Gate and obtain Story Approval again before sequence changes can continue.");
    }
    return { pass: true, initial_lock_required: false, fingerprint: actual };
  }
  if (specLocked || specFingerprint) {
    throw new Error("Story Sequence Lock is not mirrored in PROJECT_STATE. Reset Story Gate and return to Story Review before continuing.");
  }
  if (!allowInitialLock) {
    throw new Error("Story Sequence Lock is missing after Story Approval. Reset Story Gate and return to Story Review before continuing.");
  }
  return { pass: true, initial_lock_required: true, fingerprint: actual };
}

export const STORY_MUTATING_OPERATIONS = Object.freeze([...MUTATING_OPERATIONS]);
