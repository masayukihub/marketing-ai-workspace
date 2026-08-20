const INTERNAL_TOKENS = [
  "理解产品", "产生兴趣", "核心优势", "用户问题", "设计目的", "素材需求", "风险", "待确认", "需要确认", "被阻塞",
  "Need Verification", "Claim Source", "Source Ready", "Need Cutout", "Need Composition", "Need Lifestyle Generation",
  "Need Copy", "Final Ready", "Product Knowledge", "Purpose", "Review Draft", "Placeholder", "Prototype", "Visual Unit",
];

const TEMPLATE_NAMES = {
  "SB-A01": "Hero",
  "SB-A02": "50/50 Feature",
  "SB-A03": "Three Feature Grid",
  "SB-A04": "Lifestyle Full Image",
  "SB-A05": "Technical Diagram",
  "SB-A06": "Ecosystem",
  "SB-A07": "Comparison / Fit",
  "SB-A08": "FAQ / Purchase Confidence",
};

function clean(value) {
  return String(value ?? "").replaceAll("|", "\\|").replaceAll("\n", "<br>");
}

function table(headers, rows) {
  return [`| ${headers.map(clean).join(" | ")} |`, `| ${headers.map(() => "---").join(" | ")} |`, ...rows.map((row) => `| ${row.map(clean).join(" | ")} |`)].join("\n");
}

function textStatus(value, kind, claimIds, approvedClaims) {
  const text = String(value || "").trim();
  const problems = [];
  if (!text) problems.push("Unnatural: empty consumer copy");
  for (const token of INTERNAL_TOKENS) if (text.includes(token)) problems.push(`Unnatural: internal token '${token}'`);
  if (kind === "Headline" && [...text].length > 34) problems.push(`Needs Polish: headline ${[...text].length} chars`);
  if (kind === "Body" && [...text].length > 180) problems.push(`Needs Polish: body ${[...text].length} chars`);
  const unapproved = (claimIds || []).filter((id) => !approvedClaims.has(id));
  if (unapproved.length) problems.push(`Claim Risk: ${unapproved.join(", ")}`);
  if (!/[ぁ-んァ-ヶ一-龠々]/u.test(text) && !/^[\d\sA-Za-z+_.:/()×・-]+$/.test(text)) problems.push("Unnatural: Japanese consumer wording not detected");
  return problems.length ? problems.join("; ") : "Natural";
}

function consumerCopyRecords(data) {
  const title = data.titles[data.titles.recommendedKey] || data.titles.main;
  const records = [{ id: "TITLE", placement: "商品标题", kind: "Headline", text: title, claimIds: data.titles.claimIds || [] }];
  for (const [index, bullet] of (data.bullets || []).entries()) {
    records.push({ id: `BULLET-${index + 1}`, placement: "Bullet", kind: "Headline", text: bullet.headline, claimIds: bullet.claimIds });
    records.push({ id: `BULLET-${index + 1}-BODY`, placement: "Bullet", kind: "Body", text: bullet.body, claimIds: bullet.claimIds });
  }
  for (const image of data.images || []) {
    if (image.headline) records.push({ id: `${image.id}-H`, placement: "商品图", kind: "Headline", text: image.headline, claimIds: image.claimIds });
    if (image.subcopy) records.push({ id: `${image.id}-B`, placement: "商品图", kind: "Body", text: image.subcopy, claimIds: image.claimIds });
  }
  for (const unit of (data.aplusModules || []).flatMap((module) => module.units || [])) {
    records.push({ id: `${unit.id}-H`, placement: "A+", kind: "Headline", text: unit.headline, claimIds: unit.claimIds });
    records.push({ id: `${unit.id}-B`, placement: "A+", kind: "Body", text: unit.copy, claimIds: unit.claimIds });
  }
  for (const [index, item] of (data.faq || []).entries()) {
    records.push({ id: `FAQ-${index + 1}-Q`, placement: "FAQ", kind: "Headline", text: item.question, claimIds: item.claimIds });
    records.push({ id: `FAQ-${index + 1}-A`, placement: "FAQ", kind: "Body", text: item.answer, claimIds: item.claimIds });
  }
  return records;
}

export function buildLocalizationReview(data) {
  const approvedClaims = new Set((data.claims || []).filter((claim) => claim.status === "Approved").map((claim) => claim.id));
  const rows = consumerCopyRecords(data).map((record) => ({ ...record, result: textStatus(record.text, record.kind, record.claimIds, approvedClaims) }));
  const issues = rows.filter((row) => row.result !== "Natural");
  data.meta.japanLocalizationStatus = issues.length ? "Needs Review" : "Natural";
  const markdown = `# 日本本地化审查\n\n## 结论\n\n- 审查范围：消费者可见的 Title、Bullet、商品图、A+、FAQ。\n- 状态：**${data.meta.japanLocalizationStatus}**。\n- 问题数：${issues.length}。` +
    `\n- 原则：消费者端只显示自然日语；中文、内部状态、Claim 来源、制作说明仅出现在 Design Review。\n\n` +
    table(["ID", "位置", "类型", "消费者文案", "结果"], rows.map((row) => [row.id, row.placement, row.kind, row.text, row.result])) + "\n";
  return { rows, issues, markdown };
}

function inferredTemplate(module) {
  const sequenceMap = ["SB-A01", "SB-A02", "SB-A03", "SB-A04", "SB-A05", "SB-A07", "SB-A08"];
  return module.templateType || module.templateId || sequenceMap[Math.max(0, Number(module.sequence || 1) - 1)] || "SB-A02";
}

export function buildVisualConsistencyReview(data) {
  const imageRows = (data.images || []).map((item, index) => {
    const problems = [];
    if (!/\.jpe?g$/i.test(item.finalPath || "")) problems.push("不是最终 JPEG");
    if (!["MAIN", "A", "B", "C", "D", "E", "F"].includes(item.layoutId)) problems.push("缺少固定 Layout ID");
    if (!/\.svg$/i.test(item.wireframePath || "")) problems.push("缺少 Wireframe");
    if (item.designQaStatus !== "Pass") problems.push("Round 2 设计 QA 未通过");
    if (item.productBodyAiGenerated !== false) problems.push("产品本体 AI 状态未明确为 false");
    if (item.sourceOrigin !== "User Provided Official") problems.push("不是用户提供的官方产品素材");
    if (index === 0 && (item.headline || item.subcopy)) problems.push("主图源字段含营销文案，最终画布必须无文案");
    return [item.id, `阶段 ${index + 1}`, item.layoutId, item.sourceOrigin, item.sourceAssetType, String(item.productBodyAiGenerated), item.visualProductionStatus, problems.length ? problems.join("；") : "通过"];
  });
  const moduleRows = (data.aplusModules || []).map((module) => {
    const id = inferredTemplate(module);
    module.templateId = id;
    module.templateName = TEMPLATE_NAMES[id] || "Need Verification";
    const units = module.units || [];
    const nonJpeg = /\.jpe?g$/i.test(module.finalPath || "") ? 0 : 1;
    const nonOfficial = units.filter((unit) => unit.sourceOrigin !== "User Provided Official").length;
    const aiUnknown = units.filter((unit) => unit.productBodyAiGenerated !== false).length;
    const missingWireframe = !/\.svg$/i.test(module.wireframePath || "");
    const qaFailed = module.designQaStatus !== "Pass";
    const result = [nonJpeg && "缺少模块最终 JPEG", missingWireframe && "缺少 Wireframe", qaFailed && "Round 2 设计 QA 未通过", nonOfficial && `${nonOfficial} 个非用户官方素材`, aiUnknown && `${aiUnknown} 个产品 AI 状态不合格`].filter(Boolean).join("；") || "通过";
    return [module.id, `${id} — ${module.templateName}`, module.purpose, module.finalPath, units.length, result];
  });
  const failed = [...imageRows, ...moduleRows].filter((row) => row.at(-1) !== "通过");
  data.meta.visualConsistencyStatus = failed.length ? "Needs Review" : "Pass";
  const markdown = `# 视觉一致性报告\n\n## 结论\n\n- 状态：**${data.meta.visualConsistencyStatus}**。\n- 正式上线硬规则：产品本体必须来自用户提供的官方素材；AI 只可用于场景、人物、背景、灯光、道具和构图扩展。\n- 产品轮廓、比例、颜色、材质、Logo、按钮、接口、屏幕、配件、安装结构与实际组合不得由 AI 改写。\n- 商品图与 A+ 按购买决策顺序分工，A+ 不机械复读商品副图。\n\n## 7 张商品图\n\n` +
    table(["ID", "决策位置", "Layout", "产品来源", "素材类型", "产品本体 AI", "制作状态", "检查结果"], imageRows) +
    `\n\n## A+ 模板匹配\n\n` + table(["Module", "模板", "作用", "最终模块图", "内容单元", "检查结果"], moduleRows) + "\n";
  return { imageRows, moduleRows, failed, markdown };
}

export function statusChinese(status) {
  const map = {
    Ready: "已完成", Approved: "已批准", Confirmed: "已确认", Reviewed: "已审阅", Pass: "通过", Reject: "拒绝", "Copy Ready": "文案已完成", "Source Ready": "源素材已就绪",
    "Need Cutout": "待抠图", "Need Composition": "待合成", "Need Lifestyle Generation": "待生成场景", "Need Copy": "待文案",
    "Need Design": "待设计", "Need Verification": "待确认", "Asset Missing": "缺少素材", "Final Ready": "最终稿已就绪",
    Blocked: "被阻塞", Conflict: "有冲突", Unsupported: "不支持", Prohibited: "禁止", "Not Available": "不可用", "Not Applicable": "不适用",
  };
  return map[status] || status || "未知";
}
