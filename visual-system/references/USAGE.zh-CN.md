# Visual Pattern Memory 中文使用说明

你不需要学习新的 Skill 名称。仍然使用现有中文入口：

- 日本电商内容：`$jp-commerce-content-flow`
- 日本 EDM：`$switchbot-japan-edm`
- 市场洞察与 Campaign 入口保持不变。

## 第一次加入参考

直接说：

> 把这个页面加入我的视觉参考库：<URL / HTML / Screenshot / Existing Project>

系统会执行：

```text
Reference
→ Analyze
→ Extract reusable principles
→ Normalize
→ Tag
→ Register as CANDIDATE
→ Human Review
```

只提取信息架构、视觉节奏、组件模式、转化模式、响应式模式和设计原则。不会复制第三方 Logo、原创文案、图片、Trade Dress 或完整 Layout。

## 新项目

直接说：

> 用日本电商内容生成做 XXX。

系统会：

1. 读取 Project Memory 与 Product Truth；
2. 建立不写死 Pattern 的 `project-context.yaml`；
3. 自动对已注册 Pattern 排名；
4. 生成 `visual-profile.yaml`；
5. 高置信度时直接采用最高分方向；
6. 只有真实冲突时才请你 Review；
7. 继续现有 Planning、Claim、Production、Hardening 与 Mobile QA。

## 老项目

直接说：

> 继续 XXX。

如果项目存在有效 `visual-freeze.yaml`，系统默认继承，不会重新问视觉方向。以下情况除外：

- 你明确要求修改或探索；
- 当前渠道和 Freeze 冲突；
- 必需素材缺失；
- Pattern 已 Deprecated。

## Freeze 的人工批准

Router 不会自行把 Candidate 改成 Approved。人工复核后，Freeze 至少需要：

```yaml
status: APPROVED
active: true
human_approval:
  approved_by: "具名审批人"
  approved_at: "ISO-8601 时间"
```

批准范围只限 Freeze 中明确写出的视觉方向与文件，不自动批准 Product Truth、Claim、素材授权、上架、发布或发送。

## 优秀页面如何反向沉淀

完成并通过人工批准的页面可提出 Pattern Candidate：

1. 保留项目来源、Channel、适用类目、Consumer Goal 和素材条件；
2. 只抽象结构、节奏、组件、转化和响应式原则；
3. 历史效果没有可靠数据时写 `UNKNOWN`；
4. 先注册为 `CANDIDATE`；
5. 通过跨项目复用、对应 Channel QA 和人工 Review 后再升级为 `VALIDATED`。

## 维护者命令

```bash
python3 visual-system/routing/visual_router.py --project projects/s30-mini
python3 visual-system/routing/visual_router.py --project projects/lock-ultra-max
python3 -m unittest discover -s visual-system/tests -p 'test_*.py' -v
```
