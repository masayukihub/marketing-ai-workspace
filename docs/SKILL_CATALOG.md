# Skill Catalog

> GENERATED FILE — 由 `scripts/build_skill_inventory.py` 从 `runtime/skill-lock.json` 与仓库 `skills/*/SKILL.md` 生成。不要手工维护。

GitHub repository 是正式 Runtime Authority；`$CODEX_HOME/skills` 仅为安装镜像，实时状态由 `scripts/verify_codex_runtime.py` 验证。

## Runtime-locked Skills

| Skill | Role | User-visible | Mirror | Repository path |
| --- | --- | --- | --- | --- |
| `jp-commerce-content-flow` | `user_entry_japan_commerce_content` | true | verify_codex_runtime_required | `skills/jp-commerce-content-flow` |
| `jp-commerce-insights` | `user_entry_japan_commerce_research` | true | verify_codex_runtime_required | `skills/jp-commerce-insights` |
| `product-knowledge` | `internal_product_truth_gate` | false | verify_codex_runtime_required | `skills/product-knowledge` |
| `project-context-resolver` | `internal_project_context_router` | false | verify_codex_runtime_required | `skills/project-context-resolver` |
| `project-memory-manager` | `internal_project_memory_owner` | false | verify_codex_runtime_required | `skills/project-memory-manager` |
| `switchbot-japan-campaign` | `user_entry_japan_campaign` | true | verify_codex_runtime_required | `skills/switchbot-japan-campaign` |
| `switchbot-japan-edm` | `user_entry_japan_edm` | true | verify_codex_runtime_required | `skills/switchbot-japan-edm` |

## Other repository Skills

这些目录拥有仓库源码与 `SKILL.md`，但尚未进入 Runtime Lock；它们不是由本机安装状态反向认定的正式 Runtime。

| Skill | Repository path | Lock status |
| --- | --- | --- |
| `amazon-japan-pdp-generator` | `skills/amazon-japan-pdp-generator` | not locked |
| `amazon-listing-creative` | `skills/amazon-listing-creative` | not locked |
| `customer-review-intelligence` | `skills/customer-review-intelligence` | not locked |
| `influencer-marketing` | `skills/influencer-marketing` | not locked |
| `switchbot-campaign-review` | `skills/switchbot-campaign-review` | not locked |
