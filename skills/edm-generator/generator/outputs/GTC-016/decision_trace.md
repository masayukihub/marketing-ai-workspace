# GTC-016 Decision Trace

- Campaign Family: `TF-LAUNCH`
- Confidence: `0.98`
- Selected Template: `BLOCKED`
- Alternative: `None`
- Status: `BLOCKED`

## Why

- TSR-GATE-002: REQUIRED_INPUT_UNRESOLVED

## Campaign Classification Reasons

- Campaign Type 与冻结枚举完全匹配
- Primary Objective 命中 VSR-LAUNCH-A
- 不允许跨 Campaign Family 由分数覆盖

## Rejected Candidates

- Not available because preflight stopped selection.

## Determinism

- Structure fingerprint: `4413f4e9aa0632ae181f72733042b5a8281fccc63d427d7c6b2f4987723014e1`
- Same input + same sources: `PASS`

This trace reads the frozen v1.0 selection matrix. It does not use Tier D to override SwitchBot family boundaries.
