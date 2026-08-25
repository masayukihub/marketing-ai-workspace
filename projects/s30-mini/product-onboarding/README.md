# S30 mini Product Onboarding Pilot

本目录只登记 P0-1 入口与边界，不保存真实产品正文或 Pilot 输出。

- Market: `JP`
- Locale: `ja-JP`
- Channel: `Amazon.co.jp`
- Offer: `水箱版のみ`
- Flow: [`../../../flows/product-onboarding/README.md`](../../../flows/product-onboarding/README.md)
- Final gate: `PRODUCT_TRUTH_HUMAN_REVIEW_GATE`

真实运行必须指定 Git 仓库外的私有 Runtime，并先将本次使用的全部真实输入冻结到该 Runtime 的 `inputs/`。产出的 Product Knowledge Change 与 Product Truth 都是 Proposal；人审前不写 canonical Product Knowledge，不生成 Amazon Storyline、Gallery、图片或正式 PDP。
