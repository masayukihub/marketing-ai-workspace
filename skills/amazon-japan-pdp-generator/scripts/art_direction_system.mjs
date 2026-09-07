import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { visualProfile } from "./visual_quality_system.mjs";
import {
  buildProductSemanticContext,
  semanticIntent,
  scanSemanticContamination,
} from "./product_semantic_context.mjs";

export const PRODUCTION_METHODS = [
  "OFFICIAL_ASSET_COMPOSITE",
  "3D_RENDER",
  "REAL_PHOTOGRAPHY",
  "AI_SCENE_ONLY",
  "TECHNICAL_DIAGRAM",
  "UI_COMPOSITE",
  "ILLUSTRATION",
  "MIXED",
];

const REQUIRED_FIELDS = [
  "visual_objective", "consumer_takeaway", "hero_object", "secondary_object",
  "scene_type", "composition", "camera_angle", "product_scale", "product_position",
  "background", "lighting", "depth", "material_treatment", "human_presence",
  "lifestyle_props", "technical_annotation", "motion_action", "negative_space",
  "desktop_crop", "mobile_crop", "required_asset", "preferred_asset_source",
  "production_method", "production_method_reason", "risk", "fallback",
];

function hash(value) {
  return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function textOf(record) {
  return [record.headline, record.copy, record.sub_copy, record.key_message, record.role, record.purpose, record.story_role]
    .filter(Boolean).join(" ");
}

function intentOf(record, kind) {
  const text = textOf(record);
  if (record.id === "IMAGE-01") return "main_identity";
  if (/保証|サポート/.test(text)) return "support_closure";
  if (/K11|S20|モデル|自宅に合う一台/.test(text)) return "model_comparison";
  if (/販売セット|同梱物|SKU/.test(text)) return "exact_in_box";
  if (/水の交換方法|組み合わせ方向|接続条件/.test(text)) return "bundle_route";
  if (/ゴミ収集|ローラー洗浄|温風乾燥|充電/.test(text)) return "station_process";
  if (/タンク|フィルター|お手入れ|ブラシ類/.test(text)) return "maintenance_detail";
  if (/食べこぼし|ダイニング/.test(text)) return "dining_scenario";
  if (/毛や細かなゴミ|ペット/.test(text)) return "living_scenario";
  if (/毛足|6mm|回避設定/.test(text)) return "carpet_fit";
  if (/本体幅|280 × 280|旋回スペース/.test(text)) return "spatial_fit";
  if (/dToF|センサー/.test(text)) return "sensor_system";
  if (/買い替え|アップグレード|あきらめない/.test(text)) return "upgrade_value";
  if (kind === "gallery" && record.template_id === "P-LIFESTYLE-FULL") return "spatial_fit";
  if (record.template_id === "A-HERO" || record.template_id === "P-HERO-SPLIT") return "system_hero";
  if (/清水|汚水|ローラーへ|ローラーが|ローラー水拭き/.test(text)) return "roller_mechanism";
  return "functional_default";
}

const PRESETS = {
  main_identity: {
    visual_objective: "正確な商品識別と販売内容の確認。",
    consumer_takeaway: "何が届く商品かを一目で判断できる。",
    hero_object: "承認済み正確SKUの商品本体と、販売セットに含まれる場合のみステーション。",
    secondary_object: "承認済み同梱物のみ。",
    scene_type: "Pure white compliance field",
    composition: "単一の明確なシルエット。商品同士の重なりを避け、販売内容を曖昧にしない。",
    camera_angle: "Front 3/4",
    product_scale: "HERO",
    product_position: "Center",
    background: "Pure white #FFFFFF",
    lighting: "High-key soft studio",
    depth: "Shallow neutral product depth; no artificial environment",
    material_treatment: "公式素材の色・艶・エッジを保持し、影のみ整える。",
    human_presence: "None",
    lifestyle_props: "None",
    technical_annotation: "None",
    motion_action: "None",
    negative_space: "Amazon main-image margin only",
    desktop_crop: "2000×2000。商品全体と承認済み同梱物を安全域内に保持。",
    mobile_crop: "Square thumbnailでシルエットと構成物が判別可能。",
    required_asset: "正確SKUの公式白背景/透過Product ID pack。",
    preferred_asset_source: "User Provided Official / Official White Background or Official PNG",
    production_method: "OFFICIAL_ASSET_COMPOSITE",
    production_method_reason: "商品識別が目的であり、Sceneや推測表現は不要。",
    risk: "SKU・同梱物未確定時は主画像を確定できない。",
    fallback: "承認前は明確なPlaceholder。Amazon公開素材には使用しない。",
    what_must_be_visually_proven: "商品形状と販売セットの正確性。",
    what_does_not_need_text: "商品名、機能説明、アイコン。",
    claim_visual_evidence: "Claimなし。商品同一性の証拠が必要。",
    asset_ids: ["AD-AST-001", "AD-AST-002", "AD-AST-011"],
  },
  system_hero: {
    visual_objective: "小型本体と床洗浄システムの関係を、仕様一覧ではなく一つの価値として見せる。",
    consumer_takeaway: "置き場所に配慮しながら、吸引だけで終わらない床ケアへ進める。",
    hero_object: "S30 mini本体の公式3/4 Render。",
    secondary_object: "公式ステーションRenderとローラーの小さな機構Detail。",
    scene_type: "Brand-neutral product stage",
    composition: "商品を大きく、ステーションを奥に配置。コピー側に明確な余白を残す非対称構図。",
    camera_angle: "Front 3/4",
    product_scale: "HERO",
    product_position: "Right dominant, station behind",
    background: "Warm white to pale mint, no decorative gradient spectacle",
    lighting: "Soft Studio",
    depth: "Two-layer product depth",
    material_treatment: "プラスチック、金属、ローラー材の質感差を自然に保持。",
    human_presence: "None",
    lifestyle_props: "None",
    technical_annotation: "最小限の製品関係ラベルのみ。",
    motion_action: "本体がステーションから清掃へ出る方向感。",
    negative_space: "左35–40%を日本語Headline用に確保。",
    desktop_crop: "本体とステーションが切れず、Product Layerが画面の55%以上。",
    mobile_crop: "文案→本体→ステーションの順。商品間の前後関係を維持。",
    required_asset: "本体・ステーション公式透過Render、ローラーDetail。",
    preferred_asset_source: "User Provided Official / Official Render",
    production_method: "OFFICIAL_ASSET_COMPOSITE",
    production_method_reason: "価値の中心が正確な商品システム関係で、生成Sceneは不要。",
    risk: "未承認のセット構成を一体商品に見せない。",
    fallback: "本体のみの公式Renderで価値を表現し、セット関係は表示しない。",
    what_must_be_visually_proven: "小型本体とステーション/ローラーの製品関係。",
    what_does_not_need_text: "全機能一覧。",
    claim_visual_evidence: "寸法・機構・ステーション機能は各Claim状態に従う。",
    asset_ids: ["AD-AST-001", "AD-AST-002", "AD-AST-003"],
  },
  upgrade_value: {
    visual_objective: "吸引のみから床洗浄までへの買い替え価値を、競合比較ではなく生活タスクの変化として示す。",
    consumer_takeaway: "小型化を優先しても、床洗浄を諦める必要はない。",
    hero_object: "公式S30 mini本体Render。",
    secondary_object: "硬い床の清掃動線とローラー接地Detail。",
    scene_type: "Compact Japanese hard-floor context",
    composition: "商品を前景、床面の清掃動線を斜めに通し、テキストと衝突させない。",
    camera_angle: "Low angle",
    product_scale: "LARGE",
    product_position: "Lower right",
    background: "Bright compact Japanese dining/living floor",
    lighting: "Natural daylight",
    depth: "Environmental depth with product kept sharp",
    material_treatment: "床の反射を抑え、ローラー接地部だけ微細な質感を残す。",
    human_presence: "Indirect only; optional legs outside product path",
    lifestyle_props: "Compact chair legs, low table edge; maximum three props",
    technical_annotation: "清掃動線一本。性能数値は追加しない。",
    motion_action: "本体が家具間を進む。",
    negative_space: "上左30%をHeadline用に確保。",
    desktop_crop: "家具の全景より商品と床面関係を優先。",
    mobile_crop: "商品が横幅38%以上。家具を切っても清掃動線を残す。",
    required_asset: "公式本体3/4 Render、承認済み硬床接地Detail、空の日本住宅Scene。",
    preferred_asset_source: "Official Product Layer + licensed/AI scene without product",
    production_method: "MIXED",
    production_method_reason: "商品精度と日本住宅コンテキストを別レイヤーで管理する必要がある。",
    risk: "Sceneの家具間隔が実際の適用条件を誤認させる。",
    fallback: "Sceneを使わず公式Product Stageと床材Detailで表現。",
    what_must_be_visually_proven: "商品が硬い床を清掃する文脈。",
    what_does_not_need_text: "競合名、誇張したBefore/After。",
    claim_visual_evidence: "PositioningはPendingのまま。結果差を断定しない。",
    asset_ids: ["AD-AST-001", "AD-AST-003", "AD-AST-014"],
  },
  roller_mechanism: {
    visual_objective: "清水供給、ローラー接地、汚水回収の関係を一つの連続機構として可視化する。",
    consumer_takeaway: "床を濡らすだけではなく、拭き取った汚れを回収する構造が分かる。",
    hero_object: "工程承認済みローラー機構のMacro/Cutaway。",
    secondary_object: "清水・汚水の流路と床接触面。",
    scene_type: "Technical proof stage",
    composition: "左にローラー実物Detail、右に断面/流路。矢印は最少で、入口・接地・回収の3点だけ。",
    camera_angle: "Macro cutaway",
    product_scale: "DETAIL",
    product_position: "Mechanism centered",
    background: "High-key technical white with pale mint zones",
    lighting: "Technical soft studio",
    depth: "Controlled sectional depth",
    material_treatment: "ローラー繊維、水、床材を区別。水量や圧力を視覚的に誇張しない。",
    human_presence: "None",
    lifestyle_props: "One verified hard-floor sample only",
    technical_annotation: "清水→ローラー→汚水回収。文字はGraphic Layerで配置。",
    motion_action: "ローラー回転と水流を方向線で示す。",
    negative_space: "右上にHeadline、流路周辺に条件注記余白。",
    desktop_crop: "断面と接触面を同時に見せる。",
    mobile_crop: "Macro→3ステップ流路の縦順。ラベルを18px相当以上に保つ。",
    required_asset: "公式ローラーMacro、Engineering-approved cutaway/3D geometry、床接触Detail。",
    preferred_asset_source: "Approved 3D/engineering render + official detail",
    production_method: "3D_RENDER",
    production_method_reason: "外観写真だけでは内部流路と接触関係を証明できない。",
    risk: "未承認の圧力、水量、回転速度、清掃結果を図から暗示しない。",
    fallback: "公式ローラーClose-up + 3つのプログラムCallout。内部断面は省略。",
    what_must_be_visually_proven: "清水供給、ローラー接地、汚水回収の構造関係。",
    what_does_not_need_text: "水の移動方向、ローラー位置。",
    claim_visual_evidence: "CLM-ROLLER-MECHANISMのみ。Pressure/cleaning resultはPendingのため描かない。",
    asset_ids: ["AD-AST-003", "AD-AST-004", "AD-AST-017"],
  },
  sensor_system: {
    visual_objective: "センサーの物理配置と役割を、UIや成功率ではなく正確な位置関係で示す。",
    consumer_takeaway: "本体のどこで周囲を認識する設計か分かる。",
    hero_object: "公式Top/3/4 Product Render。",
    secondary_object: "承認済みセンサー位置。",
    scene_type: "Technical annotation",
    composition: "本体を中心に最大3本のCallout。放射状Feature一覧にしない。",
    camera_angle: "Top-down 3/4",
    product_scale: "LARGE",
    product_position: "Center",
    background: "Neutral technical white",
    lighting: "Soft Studio",
    depth: "Shallow",
    material_treatment: "センサー窓の反射と筐体差を保持。",
    human_presence: "None",
    lifestyle_props: "None",
    technical_annotation: "位置と名称のみ。認識数・成功率は表示しない。",
    motion_action: "None",
    negative_space: "Calloutの外側に十分な余白。",
    desktop_crop: "本体全体とセンサー位置を一画面で保持。",
    mobile_crop: "縦型リストへ変換し、位置番号と名称を隣接。",
    required_asset: "Engineering-approved sensor placement render。",
    preferred_asset_source: "User Provided Official / Engineering-approved render",
    production_method: "TECHNICAL_DIAGRAM",
    production_method_reason: "役割はプログラムCalloutで明確にし、商品外観は公式素材を保持する。",
    risk: "未検証の回避性能を暗示する。",
    fallback: "センサー名称を除き、公式Product Renderのみ。",
    what_must_be_visually_proven: "センサーの位置。",
    what_does_not_need_text: "筐体全体の形状。",
    claim_visual_evidence: "CLM-SENSOR-SETの現行構成のみ。",
    asset_ids: ["AD-AST-001", "AD-AST-005"],
  },
  spatial_fit: {
    visual_objective: "本体寸法だけでなく、家具間で旋回するための空間確認を促す。",
    consumer_takeaway: "幅だけでなく、向きを変える余地も購入前に確認する。",
    hero_object: "公式Top-down Product Render。",
    secondary_object: "実測した日本住宅スケールの家具間隔。",
    scene_type: "Measured Japanese 1LDK floor plan",
    composition: "Top-downで本体と家具脚を同一縮尺に配置。寸法線はGraphic Layer。",
    camera_angle: "Top-down",
    product_scale: "LARGE",
    product_position: "Lower center in measured path",
    background: "Light oak / light wood flooring",
    lighting: "Natural high-key",
    depth: "Near-flat orthographic",
    material_treatment: "床目は弱く、寸法線と商品輪郭を優先。",
    human_presence: "None",
    lifestyle_props: "Low-profile chair/table legs only",
    technical_annotation: "外形寸法と旋回確認ゾーン。推奨クリアランスは未確認なら数値化しない。",
    motion_action: "点線で旋回方向のみ。",
    negative_space: "左上に説明、寸法線周辺に安全域。",
    desktop_crop: "家具間隔の意味が分かる範囲まで表示。",
    mobile_crop: "Top-down図を中央、説明は下。家具全景は不要。",
    required_asset: "公式Top view/orthographic Render、実測日本住宅Sceneまたは図面。",
    preferred_asset_source: "Official Product Render + measured/licensed scene",
    production_method: "TECHNICAL_DIAGRAM",
    production_method_reason: "寸法と旋回確認は正確な縮尺・プログラム寸法線が必要。",
    risk: "未確認の最小通路幅や家具クリアランスを断定する。",
    fallback: "商品外形寸法のみ。旋回推奨値は表示しない。",
    what_must_be_visually_proven: "280×280×99mmの外形と旋回確認の必要性。",
    what_does_not_need_text: "家具の装飾説明。",
    claim_visual_evidence: "CLM-DIMENSIONSのみ。追加クリアランス数値は禁止。",
    asset_ids: ["AD-AST-006", "AD-AST-014"],
  },
  carpet_fit: {
    visual_objective: "ローラー持ち上げと床材設定の確認点を側面Detailで説明する。",
    consumer_takeaway: "床材や毛足に合わせた設定確認が必要。",
    hero_object: "承認済み側面/下面ローラーDetail。",
    secondary_object: "硬床とカーペット境界。",
    scene_type: "Material transition proof",
    composition: "側面Macroを主役にし、床材境界を一方向に通す。",
    camera_angle: "Side detail crop",
    product_scale: "DETAIL",
    product_position: "Center-left",
    background: "Neutral material sample",
    lighting: "Soft Studio",
    depth: "Shallow macro",
    material_treatment: "カーペット毛足を誇張せず、接地距離を正確に。",
    human_presence: "None",
    lifestyle_props: "One verified carpet sample",
    technical_annotation: "6mmはClaim承認状態に従い、条件と隣接。",
    motion_action: "Vertical lift arrow only",
    negative_space: "右側に条件注記。",
    desktop_crop: "本体全体ではなくローラーと床境界を優先。",
    mobile_crop: "Detailを横幅65%以上。条件注記を直下に置く。",
    required_asset: "公式Side/roller-lift detail、承認済み床材Sample。",
    preferred_asset_source: "Official Detail + approved material sample",
    production_method: "3D_RENDER",
    production_method_reason: "持ち上げ距離と部品関係を一貫した角度で示すため。",
    risk: "全てのカーペットで同一結果と誤認させる。",
    fallback: "公式Side Detailと設定確認文のみ。",
    what_must_be_visually_proven: "ローラー持ち上げ構造。",
    what_does_not_need_text: "持ち上げ方向。",
    claim_visual_evidence: "CLM-CARPET-LIFTの数値・条件。",
    asset_ids: ["AD-AST-007", "AD-AST-017"],
  },
  dining_scenario: {
    visual_objective: "日本のコンパクトなダイニングで、食後の硬床清掃タスクを具体化する。",
    consumer_takeaway: "日常の食べこぼし後に、家具間隔を確認して清掃を任せるイメージが持てる。",
    hero_object: "公式S30 mini本体Render。",
    secondary_object: "コンパクトダイニング、硬床、少量の安全な食べこぼし表現。",
    scene_type: "Japanese 1LDK compact dining",
    composition: "Environmental wide。低いテーブル/椅子の間を商品が通る。商品をSceneの隅に置かない。",
    camera_angle: "Environmental wide",
    product_scale: "CONTEXTUAL",
    product_position: "Lower third, clearly visible",
    background: "Light oak floor, off-white walls, compact storage",
    lighting: "Natural daylight",
    depth: "Realistic room depth",
    material_treatment: "生活感はあるが過剰に装飾しない。床の汚れは演出過多にしない。",
    human_presence: "Indirect optional; seated person cropped above waist or hands clearing table",
    lifestyle_props: "Compact table, 2 chairs, tray, one cloth; maximum four props",
    technical_annotation: "None; copy explains setup condition",
    motion_action: "Product moving after floor objects are cleared",
    negative_space: "Upper left 30% for copy; no face/text collision",
    desktop_crop: "家具スケールと商品動線を同時に見せる。",
    mobile_crop: "商品、椅子脚、硬床の関係を残し、人物は切ってよい。",
    required_asset: "空の日本1LDKダイニングScene、公式本体3/4 Render。",
    preferred_asset_source: "Licensed photography or AI scene without product + official product layer",
    production_method: "MIXED",
    production_method_reason: "日本住宅の生活感と商品外観精度を別々に管理する。",
    risk: "欧米住宅、広すぎる家具間隔、商品がSceneに埋もれる。",
    fallback: "承認済み空Sceneに公式商品を合成。人物なし。",
    what_must_be_visually_proven: "コンパクトな家具間で使用する生活文脈。",
    what_does_not_need_text: "部屋タイプや家具名。",
    claim_visual_evidence: "清掃結果のBefore/Afterは実機証拠がないため使用しない。",
    asset_ids: ["AD-AST-001", "AD-AST-014"],
  },
  living_scenario: {
    visual_objective: "細かなゴミや毛が気になる日常を、誇張した汚れ表現なしで示す。",
    consumer_takeaway: "日々の硬床ケアに取り入れる使用イメージが持てる。",
    hero_object: "公式S30 mini Product Layer。",
    secondary_object: "低いソファ、硬床、控えめなペット/毛の存在。",
    scene_type: "Compact Japanese living area",
    composition: "商品を前景の明るい床に配置し、ソファ下の余白を使用文脈にする。",
    camera_angle: "Environmental low wide",
    product_scale: "CONTEXTUAL",
    product_position: "Lower center",
    background: "Warm neutral Japanese apartment",
    lighting: "Natural ambient",
    depth: "Medium environmental depth",
    material_treatment: "毛や細かなゴミは視認できる最小量。清掃結果を捏造しない。",
    human_presence: "None; pet optional and secondary",
    lifestyle_props: "Low sofa, compact side table, one pet bed",
    technical_annotation: "None",
    motion_action: "Product approaching the concern area",
    negative_space: "Upper right for headline",
    desktop_crop: "商品をScene面積の18%以上。",
    mobile_crop: "商品を横幅35%以上。ペットより商品を大きく。",
    required_asset: "空の日本住宅Living Scene、公式本体Render、任意の権利確認済みペット。",
    preferred_asset_source: "AI scene without product or licensed photography + official product layer",
    production_method: "AI_SCENE_ONLY",
    production_method_reason: "生成対象は環境・Propsのみ。商品は後工程で公式Layerを合成する。",
    risk: "AI Sceneに商品らしき物体、Logo、UI、日本語が混入する。",
    fallback: "ペットなしの承認済み空Scene。",
    what_must_be_visually_proven: "日常の使用文脈のみ。",
    what_does_not_need_text: "ペットの説明。",
    claim_visual_evidence: "効果は実機検証前のため、清掃前後差を描かない。",
    asset_ids: ["AD-AST-001", "AD-AST-015"],
  },
  station_process: {
    visual_objective: "掃除後のステーション処理を、生活の手離れにつながる一連の流れとして示す。",
    consumer_takeaway: "清掃後に何をステーションへ任せられる設計か分かる。",
    hero_object: "公式ステーションRender。",
    secondary_object: "ゴミ収集、ローラー洗浄、温風乾燥、充電の承認済み4状態。",
    scene_type: "Ownership scene with technical process strip",
    composition: "広い日本住宅Sceneを主にし、下部に4状態を細いStripで配置。カード4枚に分断しない。",
    camera_angle: "Environmental 3/4",
    product_scale: "MEDIUM",
    product_position: "Left lower third near wall",
    background: "Compact 1LDK living/utility corner",
    lighting: "Bright natural daylight",
    depth: "Environmental depth with soft background",
    material_treatment: "ステーション外観を正確に保ち、Sceneは静かに。",
    human_presence: "Indirect optional; person leaving room, not demonstrating unverified action",
    lifestyle_props: "Low cabinet, narrow wall gap, one plant max",
    technical_annotation: "4状態名のみ。時間・温度・結果は未確認なら表示しない。",
    motion_action: "本体が帰還し、処理Stripへ視線が流れる。",
    negative_space: "右上40%をHeadlineと短いCopy用に確保。",
    desktop_crop: "ステーション周辺の日本住宅スケールを残す。",
    mobile_crop: "Scene上部→商品→4状態縦リスト。背景の空洞を作らない。",
    required_asset: "公式ステーション3/4 Render、承認済み4プロセスDetail、空の日本住宅Ownership Scene。",
    preferred_asset_source: "Official renders + licensed/AI scene without product",
    production_method: "MIXED",
    production_method_reason: "生活上の手離れと機能プロセスを、Scene/Product/Graphicの3層で分担する。",
    risk: "処理時間・乾燥結果などPending情報を絵で確定させる。",
    fallback: "公式ステーションRender + プログラム4ステップ。Sceneなし。",
    what_must_be_visually_proven: "ステーションと本体の所有関係、および承認済み処理項目。",
    what_does_not_need_text: "帰還方向と4工程の順序。",
    claim_visual_evidence: "CLM-STATION-FUNCTIONS。所要時間・結果は描かない。",
    asset_ids: ["AD-AST-002", "AD-AST-008", "AD-AST-016"],
  },
  maintenance_detail: {
    visual_objective: "定期的に触れる部品と手入れ行為を、清潔で現実的なOwnership Detailとして示す。",
    consumer_takeaway: "完全放置ではなく、確認が必要な部品が分かる。",
    hero_object: "承認済みタンク、フィルター、ローラー、ブラシ類。",
    secondary_object: "手袋なしの自然な手元、乾いた作業台。",
    scene_type: "Maintenance tabletop",
    composition: "部品を一直線に並べず、使用順に浅い奥行きで配置。",
    camera_angle: "Top-down detail",
    product_scale: "DETAIL",
    product_position: "Components centered",
    background: "Warm white utility surface",
    lighting: "Soft natural studio",
    depth: "Shallow tabletop depth",
    material_treatment: "水滴や汚れを過度に演出せず、素材差を正確に。",
    human_presence: "Hands only, optional",
    lifestyle_props: "One drying cloth; no decorative cleaning products",
    technical_annotation: "部品名のみ。交換周期は説明書確認前に表示しない。",
    motion_action: "手がタンクを外す/確認する一動作。",
    negative_space: "右側にMaintenance copy。",
    desktop_crop: "部品と手元が切れない。",
    mobile_crop: "主部品を2×2ではなく縦順で見せる。",
    required_asset: "公式Maintenance Detail、承認済み部品一式、必要なら手元撮影。",
    preferred_asset_source: "Official Detail + real photography",
    production_method: "REAL_PHOTOGRAPHY",
    production_method_reason: "Ownershipの現実感と部品の扱いを3Dだけでなく手元で示す。",
    risk: "未確認の交換頻度、洗い方、食洗機対応などを示唆する。",
    fallback: "公式部品Renderをプログラム配列。手元なし。",
    what_must_be_visually_proven: "確認対象となる部品。",
    what_does_not_need_text: "手の動作。",
    claim_visual_evidence: "CLM-MAINTENANCE。説明書未確認項目はラベルのみ。",
    asset_ids: ["AD-AST-009", "AD-AST-013"],
  },
  bundle_route: {
    visual_objective: "水交換/設置方式の選択肢を、SKU確定後に誤解なく示す。",
    consumer_takeaway: "設置方式によって必要条件が異なるため、購入前確認が必要。",
    hero_object: "承認済み各Bundleの公式Render。",
    secondary_object: "給排水/タンクの関係を示すプログラム接続図。",
    scene_type: "Technical selection diagram",
    composition: "左右2ルートを同一縮尺で比較。中央に優劣表現を置かない。",
    camera_angle: "Isometric",
    product_scale: "MEDIUM",
    product_position: "Balanced left/right",
    background: "Neutral white",
    lighting: "Soft Studio",
    depth: "Shallow isometric",
    material_treatment: "公式Bundle形状を保持。接続線はGraphic Layer。",
    human_presence: "None",
    lifestyle_props: "Only verified plumbing/space symbols",
    technical_annotation: "正式名称、同梱物、接続条件確定後のみ。",
    motion_action: "None",
    negative_space: "各ルート上部に名称、下部に条件。",
    desktop_crop: "2ルート全体を同一画面。",
    mobile_crop: "左右比較を縦順にし、各条件を対象の直下に置く。",
    required_asset: "正式SKU/Bundleの公式Render、承認済み接続図。",
    preferred_asset_source: "User Provided Official / Approved engineering diagram",
    production_method: "TECHNICAL_DIAGRAM",
    production_method_reason: "選択条件と接続関係を正確に管理する必要がある。",
    risk: "現時点でSKU・名称・同梱物・接続条件がBlocked。",
    fallback: "内部Review用Placeholderのみ。消費者Artworkは生成しない。",
    what_must_be_visually_proven: "確定後の二つの設置方式と前提条件。",
    what_does_not_need_text: "単純な接続方向。",
    claim_visual_evidence: "CLM-BUNDLE-DIRECTION / CLM-WATER-INSTALLがApprovedになるまでBlocked。",
    asset_ids: ["AD-AST-010"],
  },
  model_comparison: {
    visual_objective: "S30 mini、K11+ Pro、S20を優劣ではなく適合条件で選べるようにする。",
    consumer_takeaway: "自宅の床ケアと設置スペースに合うモデルを判断できる。",
    hero_object: "各モデルの承認済み公式Packshot。",
    secondary_object: "プログラムComparison rows。",
    scene_type: "Editorial comparison",
    composition: "全モデル同一縮尺・同一視点。比較項目は選択に必要なものだけ。",
    camera_angle: "Front",
    product_scale: "MEDIUM",
    product_position: "Aligned comparison row",
    background: "White with restrained rule lines",
    lighting: "Consistent soft studio",
    depth: "Flat editorial",
    material_treatment: "各公式素材の色調差を過度に均一化しない。",
    human_presence: "None",
    lifestyle_props: "None",
    technical_annotation: "Current source-backed comparison only。",
    motion_action: "None",
    negative_space: "商品名と選択理由を近接。",
    desktop_crop: "3モデルと主要行を同時表示。",
    mobile_crop: "モデル別カードではなく、優先条件→該当モデルの縦順。",
    required_asset: "S30 mini、K11+ Pro、S20の承認済み公式Packshot。",
    preferred_asset_source: "User Provided Official / approved current model assets",
    production_method: "OFFICIAL_ASSET_COMPOSITE",
    production_method_reason: "比較の信頼性は同一基準の公式Product Layerに依存する。",
    risk: "比較値がPendingのまま優劣を断定する。",
    fallback: "確認済み差分だけのテキスト選択ガイド。",
    what_must_be_visually_proven: "モデル外観とサイズ感の相対比較。",
    what_does_not_need_text: "製品カテゴリの共通点。",
    claim_visual_evidence: "CLM-COMPARISON-DRAFT承認前は内部Review限定。",
    asset_ids: ["AD-AST-001", "AD-AST-012"],
  },
  exact_in_box: {
    visual_objective: "販売セット、同梱物、設置条件を正確SKU単位で確認できるようにする。",
    consumer_takeaway: "購入後に不足・誤認が起きない。",
    hero_object: "正確SKUの同梱物Flat lay。",
    secondary_object: "別売/必須条件のプログラムチェック。",
    scene_type: "In-box inventory",
    composition: "Top-down flat lay。付属品と別売品を明確に分離。",
    camera_angle: "Top-down",
    product_scale: "DETAIL",
    product_position: "Grid-aligned",
    background: "Pure warm white",
    lighting: "High-key studio",
    depth: "Flat lay",
    material_treatment: "全構成物を同じ色基準で撮影。",
    human_presence: "None",
    lifestyle_props: "None",
    technical_annotation: "同梱/別売/必要条件のみ。",
    motion_action: "None",
    negative_space: "ラベルと境界線用に十分な余白。",
    desktop_crop: "全構成物を一画面。",
    mobile_crop: "主商品→同梱→別売/条件の縦順。",
    required_asset: "承認済み正確SKUのIn-box撮影または公式Render。",
    preferred_asset_source: "User Provided Official / Real photography",
    production_method: "REAL_PHOTOGRAPHY",
    production_method_reason: "同梱物は抽象図より正確な現物一覧が必要。",
    risk: "現時点で商品名、SKU、同梱物、価格が未確定。",
    fallback: "内部ReviewのBlocked checklistのみ。",
    what_must_be_visually_proven: "実際に同梱される全構成物。",
    what_does_not_need_text: "外観説明。",
    claim_visual_evidence: "CLM-BUNDLE-DIRECTIONがApprovedになるまで公開不可。",
    asset_ids: ["AD-AST-011"],
  },
  support_closure: {
    visual_objective: "未承認の保証年数を足さず、公式サポート導線で静かに購入を収束する。",
    consumer_takeaway: "購入後の確認先が分かる。",
    hero_object: "公式S30 miniまたはSwitchBot Brand asset。",
    secondary_object: "承認済みサポートアイコン/窓口表現。",
    scene_type: "Quiet brand closure",
    composition: "低密度。商品を小さな安心のAnchorにし、FAQ Copyを主役にする。",
    camera_angle: "Front",
    product_scale: "MEDIUM",
    product_position: "Right lower third",
    background: "Warm white",
    lighting: "Soft ambient",
    depth: "Flat editorial",
    material_treatment: "公式Brand assetのみ。",
    human_presence: "None",
    lifestyle_props: "None",
    technical_annotation: "None",
    motion_action: "None",
    negative_space: "FAQ/条件文のための広い余白。",
    desktop_crop: "商品とFAQを一画面。",
    mobile_crop: "質問→回答→商品Anchorの順。",
    required_asset: "承認済みSwitchBot Brand/support asset、公式商品Render。",
    preferred_asset_source: "User Provided Official",
    production_method: "OFFICIAL_ASSET_COMPOSITE",
    production_method_reason: "Brand closureは公式素材と承認済み文言だけで構成する。",
    risk: "保証期間、対応範囲、No.1等を未承認のまま示す。",
    fallback: "商品RenderなしのプログラムFAQ。",
    what_must_be_visually_proven: "公式サポート導線の存在のみ。",
    what_does_not_need_text: "抽象的な安心表現。",
    claim_visual_evidence: "CLM-SUPPORT-PENDING承認前は具体条件を表示しない。",
    asset_ids: ["AD-AST-001", "AD-AST-018"],
  },
  functional_default: {
    visual_objective: "一つの消費者質問に対して、公式商品と必要最小限の視覚証拠を対応させる。",
    consumer_takeaway: "機能の意味と購入判断への関係が分かる。",
    hero_object: "承認済み公式Product Layer。",
    secondary_object: "一つのSource-backed Detail。",
    scene_type: "Functional product stage",
    composition: "非対称のProduct + Proof。",
    camera_angle: "Side",
    product_scale: "LARGE",
    product_position: "Center-right",
    background: "Neutral high-key",
    lighting: "Soft Studio",
    depth: "Controlled",
    material_treatment: "公式素材の材質を保持。",
    human_presence: "None",
    lifestyle_props: "None",
    technical_annotation: "最大2点。",
    motion_action: "Only when source-backed",
    negative_space: "Copy側35%。",
    desktop_crop: "商品全体とProofを保持。",
    mobile_crop: "Copy→商品→Proof。",
    required_asset: "公式Product Renderと承認済みDetail。",
    preferred_asset_source: "User Provided Official",
    production_method: "OFFICIAL_ASSET_COMPOSITE",
    production_method_reason: "最小限の正確なProduct/Proof関係を作る。",
    risk: "証拠のない装飾Callout。",
    fallback: "公式Product Renderのみ。",
    what_must_be_visually_proven: "商品と機能部位の関係。",
    what_does_not_need_text: "視認できる部位。",
    claim_visual_evidence: "紐づくClaimのApproved範囲のみ。",
    asset_ids: ["AD-AST-001"],
  },
};

const ASSET_CATALOG = [
  ["AD-AST-001", "S30 mini official robot cutout", "P0", "Official PNG/Render", "Front and 3/4; transparent", "At least 3000px long edge", "Transparent PNG", "Exact JP Product ID", "Soft Studio", "None", "All product visuals", "Creative/PM", "MISSING", "No consumer final; explicit placeholder"],
  ["AD-AST-002", "S30 mini official station cutout", "P0", "Official PNG/Render", "Front 3/4 and side", "At least 3000px long edge", "Transparent PNG", "Exact intended station", "Soft Studio", "None", "Station function/bundle Claims", "Creative/PM", "MISSING", "Product-only module without station claims"],
  ["AD-AST-003", "Official roller macro", "P0", "Official Detail/3D", "Underside macro", "At least 2400px long edge", "Transparent or neutral", "Clean roller installed", "Technical soft studio", "Hard-floor sample", "CLM-ROLLER-MECHANISM", "3D/Engineering", "MISSING", "Approved external close-up, no cutaway"],
  ["AD-AST-004", "Engineering-approved water-flow cutaway", "P0", "3D Render", "Exploded/cutaway", "4K master", "Alpha + layered source", "Approved clean/dirty-water geometry", "Technical", "Verified hard floor", "CLM-ROLLER-MECHANISM; no pressure/result claim", "3D/Engineering", "MISSING", "Official roller macro + programmatic 3-step arrows"],
  ["AD-AST-005", "Engineering-approved sensor placement render", "P0", "Official/3D Detail", "Top-down 3/4", "At least 2400px", "Transparent PNG", "Current sensor configuration", "Soft Studio", "None", "CLM-SENSOR-SET", "3D/Engineering", "MISSING", "Product render without performance callouts"],
  ["AD-AST-006", "Official top-view orthographic render", "P0", "3D Render", "Top-down orthographic", "At least 2400px", "Transparent PNG", "Exact body outline", "High-key", "Measured scale reference", "CLM-DIMENSIONS", "3D/Engineering", "MISSING", "Official 3/4 render; dimensions only"],
  ["AD-AST-007", "Official roller-lift side detail", "P0", "3D Render", "Side macro", "At least 2400px", "Transparent PNG", "Verified lift state", "Technical", "Approved carpet sample", "CLM-CARPET-LIFT", "3D/Engineering", "MISSING", "Side detail without lift-distance graphic"],
  ["AD-AST-008", "Approved station process state pack", "P0", "Official Detail/3D", "Consistent 3/4", "4 frames at 2000px+", "Transparent PNG", "Collection/wash/dry/charge states", "Consistent soft studio", "None", "CLM-STATION-FUNCTIONS", "3D/Engineering", "MISSING", "Station hero + programmatic labels only"],
  ["AD-AST-009", "Official maintenance component pack", "P0", "Official Detail", "Top/3/4 details", "At least 2000px each", "Transparent PNG", "Tank/filter/roller/brush current parts", "Soft Studio", "Utility surface optional", "CLM-MAINTENANCE", "Product/CS", "MISSING", "Text checklist; no handling photo"],
  ["AD-AST-010", "Approved exact bundle renders", "P0", "Official Render", "Isometric consistent", "At least 3000px each", "Transparent PNG", "Final SKU/name/in-box/connection", "Soft Studio", "Verified connection context", "CLM-BUNDLE-DIRECTION; CLM-WATER-INSTALL", "PM/3D", "BLOCKED", "Internal placeholder only"],
  ["AD-AST-011", "Exact-SKU in-box flat lay", "P0", "Real Photography", "Top-down", "4K master", "White background", "Final JP sales set", "High-key", "No extra props", "CLM-BUNDLE-DIRECTION", "Photo/PM", "BLOCKED", "Internal checklist only"],
  ["AD-AST-012", "Current K11+ Pro and S20 official packshots", "P0", "Official PNG/Render", "Front, scale-consistent", "At least 2400px each", "Transparent PNG", "Current JP models", "Soft Studio", "None", "CLM-COMPARISON-DRAFT", "Brand/EC", "PARTIAL", "Text-only verified differences"],
  ["AD-AST-013", "Maintenance hands tabletop photo", "P1", "Real Photography", "Top-down detail", "4K master", "Licensed RAW/JPEG", "Approved maintenance action", "Natural soft", "Warm-white utility surface", "CLM-MAINTENANCE", "Photo", "MISSING", "Official component pack without hands"],
  ["AD-AST-014", "Compact Japanese 1LDK dining scene without product", "P1", "Licensed Photo or AI Scene Only", "Environmental wide/top variant", "4K master", "Layered/clean plate", "Empty scene; no product/logo/text/UI", "Natural daylight", "Light oak, compact table, 2 chairs", "No performance claim", "Photo/AI Scene", "MISSING", "Neutral measured diagram"],
  ["AD-AST-015", "Compact Japanese living scene without product", "P1", "Licensed Photo or AI Scene Only", "Environmental low wide", "4K master", "Layered/clean plate", "Empty scene; optional licensed pet", "Natural ambient", "Low sofa, small side table", "No cleaning-result claim", "Photo/AI Scene", "MISSING", "Pet-free warm-neutral room"],
  ["AD-AST-016", "Japanese ownership scene for station", "P1", "Licensed Photo or AI Scene Only", "Environmental 3/4", "4K master", "Layered/clean plate", "Empty compact wall/utility corner", "Bright daylight", "Low cabinet, one plant max", "No station-performance claim", "Photo/AI Scene", "MISSING", "Neutral studio stage"],
  ["AD-AST-017", "Approved floor/material contact samples", "P1", "Material photography/3D", "Macro/side", "At least 2000px", "Layered", "Verified hard floor and carpet samples", "Technical soft", "No decorative props", "Roller/contact/lift Claims", "3D/Engineering", "MISSING", "Neutral material swatch"],
  ["AD-AST-018", "Approved SwitchBot support/brand closure asset", "P0", "Official Brand Asset", "Front/editorial", "At least 2000px", "Transparent/vector", "Current approved JP support expression", "Soft ambient", "None", "CLM-SUPPORT-PENDING", "Brand/CS/Legal", "BLOCKED", "Programmatic FAQ without concrete support term"],
].map(([asset_id,purpose,priority,shot_render_type,angle,resolution,transparency,required_product_state,lighting,scene_requirement,claim_dependency,owner,status,fallback])=>({asset_id,used_in:[],purpose,priority,shot_render_type,angle,crop:"Desktop and mobile-safe variants required",resolution,transparency,required_product_state,lighting,scene_requirement,claim_dependency,owner,status,fallback}));

function compactContext(context) {
  return {
    product: context.product,
    category_id: context.category_id,
    category_name: context.category_name,
    source: context.source,
    context_sha256: context.context_sha256,
    quality_priority: context.quality_priority,
  };
}

function methodFor(intent) {
  return ({
    main_identity: "OFFICIAL_ASSET_COMPOSITE",
    compatibility_fit: "TECHNICAL_DIAGRAM",
    installation: "REAL_PHOTOGRAPHY",
    unlock_scenario: "MIXED",
    power_exception: "3D_RENDER",
    security_trust: "TECHNICAL_DIAGRAM",
    configuration: "OFFICIAL_ASSET_COMPOSITE",
    support_closure: "ILLUSTRATION",
    daily_routine: "AI_SCENE_ONLY",
    functional_default: "OFFICIAL_ASSET_COMPOSITE",
  })[intent] || "OFFICIAL_ASSET_COMPOSITE";
}

function directionFor(intent, context) {
  const product = context.product.name;
  const common = {
    product_scale: "LARGE",
    product_position: "Right",
    background: "Warm white / pale mint, with no decorative spectacle",
    lighting: "Soft studio daylight",
    depth: "Controlled product-first depth",
    material_treatment: "Preserve the official product material, edge, colour and surface finish.",
    human_presence: "None unless a verified human action is required to explain use.",
    lifestyle_props: "No more than three category-relevant props.",
    technical_annotation: "Programmatic labels only; no text baked into imagery.",
    motion_action: "None unless the consumer question requires an action sequence.",
    negative_space: "Reserve 32–40% for approved Japanese copy.",
    desktop_crop: "Keep the complete Product Layer and the primary proof within the desktop safe area.",
    mobile_crop: "Copy first, proof second; keep product identity and all conditions visible at 390px.",
    preferred_asset_source: "User-provided usage-approved official asset",
    fallback: "Use an explicit review-only placeholder; do not imply the missing product fact.",
    what_does_not_need_text: "Product silhouette and visible physical relationships already shown by the official asset.",
  };
  const presets = {
    main_identity: {
      visual_objective: `Identify ${product} and the exact sales set without ambiguity.`,
      consumer_takeaway: "I understand what product is being offered and what is included.",
      hero_object: `Usage-approved official ${product} Product ID asset.`,
      secondary_object: "Only confirmed in-box items belonging to the exact SKU.",
      scene_type: "Pure white Amazon product field",
      composition: "One dominant, unobstructed product silhouette; confirmed items remain clearly separable.",
      camera_angle: "Front three-quarter",
      product_scale: "HERO",
      product_position: "Center",
      background: "Pure white #FFFFFF",
      lighting: "High-key soft studio",
      required_asset: `Exact-SKU official ${product} packshot and confirmed in-box assets.`,
      production_method_reason: "Identity and exact-SKU accuracy require official assets only.",
      risk: "SKU or included-item uncertainty can misrepresent what is sold.",
      what_must_be_visually_proven: "Product identity and exact sales-set boundaries.",
      claim_visual_evidence: "No performance claim; Product ID evidence only.",
    },
    compatibility_fit: {
      visual_objective: "Turn compatibility uncertainty into a checkable purchase step.",
      consumer_takeaway: "I know what measurements and physical relationships must be checked before purchase.",
      hero_object: `Official ${product} installed-side asset or approved outline.`,
      secondary_object: "Engineering-approved door, thumbturn and clearance geometry.",
      scene_type: "Measured compatibility diagram",
      composition: "One central fit diagram with no more than three ordered verification points.",
      camera_angle: "Orthographic / measured side view",
      required_asset: "Engineering-approved compatibility geometry and current Japan compatibility guide.",
      production_method_reason: "Fit requires exact geometry and programmatic measurement labels.",
      risk: "Universal-fit implications or invented dimensions are prohibited.",
      what_must_be_visually_proven: "The physical relationships that determine fit.",
      claim_visual_evidence: "Only approved dimensions and compatibility conditions.",
    },
    installation: {
      visual_objective: "Show the verified mounting order and the point at which fit must be confirmed.",
      consumer_takeaway: "I understand how installation is approached and what must be checked first.",
      hero_object: `Official ${product} in a verified installed state.`,
      secondary_object: "Real door surface, hand action and approved mounting parts.",
      scene_type: "Verified installation sequence",
      composition: "Three ordered steps with one action per frame and no hidden product state.",
      camera_angle: "Door-side close-up",
      required_asset: "Usage-approved real installation photography and approved setup sequence.",
      production_method_reason: "A real, reproducible hand action is more credible than a conceptual render.",
      risk: "An incorrect order, adhesive state or door type can create unsafe guidance.",
      what_must_be_visually_proven: "Mounting position, action order and verified product state.",
      claim_visual_evidence: "Approved installation instructions only.",
    },
    unlock_scenario: {
      visual_objective: "Separate the lock body role from the input method used in a household scenario.",
      consumer_takeaway: "I can decide which entry method and accessory configuration fits each person.",
      hero_object: `Official ${product} installed indoors.`,
      secondary_object: "A licensed Japanese entryway moment and only the confirmed corresponding accessory.",
      scene_type: "Japanese household entry scenario",
      composition: "Human action leads; product and accessory ownership remain visually distinct.",
      camera_angle: "Eye-level entryway crop",
      required_asset: "Official installed-product asset, approved accessory asset and licensed/approved entryway scene.",
      production_method_reason: "Official Product Layers must be composited into a credible category-specific scene.",
      risk: "Do not assign accessory authentication capability to the lock body.",
      what_must_be_visually_proven: "Which component performs each action in the scenario.",
      claim_visual_evidence: "Approved capability-owner map.",
    },
    power_exception: {
      visual_objective: "Explain power and exception handling without a zero-risk promise.",
      consumer_takeaway: "I know which failure states and fallback steps must be confirmed.",
      hero_object: `Engineering-approved ${product} power-state render.`,
      secondary_object: "Approved alert, manual and physical-key relationship states.",
      scene_type: "Exception-state technical flow",
      composition: "A short state flow: normal → alert → verified fallback, with conditions adjacent.",
      camera_angle: "Technical cutaway / state sequence",
      required_asset: "Approved power architecture, exception flow and support-reviewed wording.",
      production_method_reason: "Internal relationships need approved geometry and a programmatic state flow.",
      risk: "Absolute safety, duration or lockout-prevention implications are prohibited.",
      what_must_be_visually_proven: "Verified state transitions and ownership of each fallback.",
      claim_visual_evidence: "Approved power and exception-state source only.",
    },
    security_trust: {
      visual_objective: "Build trust by separating lock operation, communication and unsupported assumptions.",
      consumer_takeaway: "I understand what is known, what depends on connection and what still needs confirmation.",
      hero_object: `Official ${product} operation-state asset.`,
      secondary_object: "Programmatic dependency and state map.",
      scene_type: "Trust and dependency diagram",
      composition: "Product at the centre; no more than three verified state or dependency callouts.",
      camera_angle: "Front technical view",
      required_asset: "Approved operation-state assets and reviewed dependency definitions.",
      production_method_reason: "Trust depends on explicit state and dependency ownership, not dramatic imagery.",
      risk: "Do not imply absolute security, guaranteed availability or an unapproved remote function.",
      what_must_be_visually_proven: "Verified operational state and dependency boundaries.",
      claim_visual_evidence: "Approved state, communication and support sources.",
    },
    configuration: {
      visual_objective: "Help shoppers distinguish the lock body, optional accessories and exact sales set.",
      consumer_takeaway: "I know which configuration is relevant to the way I want to use the product.",
      hero_object: `Official ${product} packshot.`,
      secondary_object: "Exact current accessory packshots, each with its own capability label.",
      scene_type: "Configuration comparison",
      composition: "Consistent-scale official packshots above programmatic comparison rows.",
      camera_angle: "Front / isometric matched set",
      required_asset: "Exact-SKU official packshots and approved capability-owner table.",
      production_method_reason: "Configuration accuracy requires official packshots and a programmatic table.",
      risk: "Do not infer bundle contents, price, accessory compatibility or included items.",
      what_must_be_visually_proven: "The product-to-accessory relationship and exact SKU boundary.",
      claim_visual_evidence: "Approved SKU and capability-owner source.",
    },
    support_closure: {
      visual_objective: "Close purchase uncertainty with a clear pre-installation confirmation path.",
      consumer_takeaway: "I know what information to prepare and where to confirm unresolved fit questions.",
      hero_object: `Official ${product} silhouette or approved support illustration.`,
      secondary_object: "Programmatic checklist and support path.",
      scene_type: "Support closure",
      composition: "One calm product anchor plus a short ordered checklist.",
      camera_angle: "Front editorial",
      required_asset: "Current Japan support path and usage-approved brand asset.",
      production_method_reason: "A simple illustration and programmatic checklist avoid inventing a product state.",
      risk: "Do not publish obsolete support routes or unconfirmed service terms.",
      what_must_be_visually_proven: "What shoppers should prepare before asking for fit support.",
      claim_visual_evidence: "Current approved Japan support source.",
    },
    daily_routine: {
      visual_objective: "Show a believable Japanese entryway ownership moment without generating the product.",
      consumer_takeaway: "I can imagine how the product fits into a normal household routine.",
      hero_object: `Official ${product} composited after scene production.`,
      secondary_object: "Japanese apartment entryway and restrained human action.",
      scene_type: "Compact Japanese entryway",
      composition: "Scene-first clean plate with reserved geometry for the official Product Layer.",
      camera_angle: "Natural eye-level wide",
      required_asset: "Licensed or AI-generated empty entryway clean plate plus official product asset.",
      production_method_reason: "AI may provide the empty scene only; the product is added from official assets.",
      risk: "Generated product, logo, Japanese copy, UI or inaccurate installation geometry is prohibited.",
      what_must_be_visually_proven: "A credible ownership context, not a performance result.",
      claim_visual_evidence: "No new product claim.",
    },
  };
  const selected = presets[intent] || {
    visual_objective: `Explain the current purchase question for ${product} with source-bounded evidence.`,
    consumer_takeaway: "I understand the next purchase decision without an unsupported claim.",
    hero_object: `Usage-approved official ${product} asset.`,
    secondary_object: "Only verified category-relevant evidence.",
    scene_type: "Product-first explanatory field",
    composition: "One product anchor, one proof anchor and sufficient copy space.",
    camera_angle: "Front three-quarter",
    required_asset: `Usage-approved official ${product} asset and approved proof material.`,
    production_method_reason: "A source-bounded official composite is the safest fallback.",
    risk: "Missing product truth must remain visible as unresolved.",
    what_must_be_visually_proven: "Only the verified relationship needed for the current decision.",
    claim_visual_evidence: "Approved Claim source only.",
  };
  return { ...common, ...selected };
}

function buildRecord(record, kind, context, module = null) {
  const intent = semanticIntent(record, context);
  const direction = directionFor(intent, context);
  const profile = visualProfile(kind === "gallery" ? record : module, kind === "gallery" ? "gallery" : "aplus", context);
  const method = methodFor(intent);
  const assetId = `AD-${record.id}`;
  return {
    id: record.id,
    module_id: module?.id || null,
    sequence: kind === "gallery" ? record.sequence : module?.sequence,
    kind,
    stage: record.stage || module?.story_role || "Not Available",
    story_role: record.role || record.purpose || module?.story_role || "Not Available",
    visual_role: profile.visual_role,
    template_id: record.template_id || module?.template_id,
    intent,
    frozen_headline: record.headline || "",
    frozen_copy: record.copy || record.sub_copy || "",
    claim_ids: record.claim_ids || [],
    claim_source: record.claim_source || "Not Available",
    content_status: record.status || module?.module_availability || "Need Verification",
    ...direction,
    product_scale: String(profile.product_scale || direction.product_scale).toUpperCase(),
    product_position: profile.product_position || direction.product_position,
    decision_reason: profile.decision_reason || "",
    production_method: method,
    asset_ids: [assetId],
    product_layer_rule: "Official/verified/usage-approved product asset only; product_body_ai_generated=false",
    scene_layer_rule: "AI may create environment/background/non-product props only; no product, logo, Japanese, UI or technical text",
    graphic_layer_rule: "All Japanese copy, callouts, arrows, diagrams and tables are programmatic HTML/CSS/SVG",
    semantic_relevance: { status: "PASS", category_id: context.category_id, intent },
  };
}

function moduleDirection(module, units, context) {
  const profile = visualProfile(module, "aplus", context);
  return {
    id: module.id,
    sequence: module.sequence,
    story_role: module.story_role,
    visual_role: profile.visual_role,
    template_id: module.template_id,
    wireframe_path: module.outputs?.wireframe_svg || "",
    current_visual_path: module.outputs?.jpeg || "",
    current_art_direction: "Deterministic template render; missing production assets remain explicit placeholders.",
    visual_objective: `Answer the module's ${module.story_role} purchase task as one visual composition.`,
    recommended_art_direction: `${units[0]?.composition || "One evidence anchor"} Production methods: ${[...new Set(units.map((unit) => unit.production_method))].join(" + ")}.`,
    pilot_note: "Units share one module canvas. Product, scene and graphic layers remain separate; no Unit becomes a free-form banner.",
    required_assets: [...new Set(units.flatMap((unit) => unit.asset_ids))],
    production_methods: [...new Set(units.map((unit) => unit.production_method))],
    mobile_crop: units.map((unit) => `${unit.id}: ${unit.mobile_crop}`).join(" | "),
    risks: [...new Set(units.map((unit) => unit.risk))],
    semantic_relevance: { status: "PASS", category_id: context.category_id },
    units,
  };
}

function buildAssets(records, context) {
  return records.map((record) => ({
    asset_id: record.asset_ids[0],
    used_in: [record.id],
    purpose: record.required_asset,
    priority: record.id === "IMAGE-01" || ["compatibility_fit", "installation", "power_exception", "configuration"].includes(record.intent) ? "P0" : "P1",
    shot_render_type: record.production_method,
    angle: record.camera_angle,
    crop: `${record.desktop_crop} / ${record.mobile_crop}`,
    resolution: record.kind === "gallery" ? "2000×2000 master" : "1464×600 or approved responsive master",
    transparency: /OFFICIAL|3D|TECHNICAL/.test(record.production_method) ? "Layered PNG/SVG required" : "Layered clean plate required",
    required_product_state: `Verified current ${context.product.name} state for ${record.intent}`,
    lighting: record.lighting,
    scene_requirement: record.scene_type,
    claim_dependency: (record.claim_ids || []).join(", ") || "No performance Claim",
    owner: /TECHNICAL|3D/.test(record.production_method) ? "Product / Engineering / Design" : "Marketing / Design / Product",
    status: "MISSING",
    fallback: record.fallback,
  }));
}

function repeatedRuns(records, field) {
  const runs=[]; let start=0;
  for(let i=1;i<=records.length;i+=1){
    if(i<records.length&&records[i][field]===records[start][field]) continue;
    const run = records.slice(start,i);
    if(i-start>=3 && !run.every((record) => record.decision_reason)) runs.push({field,value:records[start][field],ids:run.map(r=>r.id)});
    start=i;
  }
  return runs;
}

export function buildArtDirectionSpec(spec) {
  const context = buildProductSemanticContext(spec);
  const gallery = spec.product_images.map((item) => buildRecord(item, "gallery", context));
  const unitRecords = spec.aplus_modules.flatMap((module) => module.units.map((unit) => buildRecord(unit, "aplus_unit", context, module)));
  const aplus = spec.aplus_modules.map((module) => moduleDirection(module, unitRecords.filter((unit) => unit.module_id === module.id), context));
  const assets = buildAssets([...gallery, ...unitRecords], context);
  const methodCounts = [...gallery,...unitRecords].reduce((acc,item)=>(acc[item.production_method]=(acc[item.production_method]||0)+1,acc),{});
  const moduleAnchors = aplus.map((module) => module.units[0]).filter(Boolean);
  const cameraWarnings=[...repeatedRuns(gallery,"camera_angle"),...repeatedRuns(moduleAnchors,"camera_angle")];
  const scaleWarnings=[...repeatedRuns(gallery,"product_scale"),...repeatedRuns(moduleAnchors,"product_scale")];
  const semantic = scanSemanticContamination({ gallery, aplus_modules: aplus, asset_requirements: assets }, context);
  const score = {
    semantic_relevance: semantic.status === "PASS" ? 100 : 0,
    product_focus:null,
    visual_proof:null,
    scene_authenticity:null,
    camera_variety:null,
    product_scale_rhythm:null,
    material_lighting_fit:null,
    jp_lifestyle_fit:null,
    brand_fit:null,
    production_feasibility:null,
  };
  score.overall = null;
  return {
    schema_version:"1.0",
    system:"Amazon Japan PDP Art Direction Layer",
    status: semantic.status === "PASS" ? "READY_FOR_HUMAN_REVIEW" : "BLOCKED_SEMANTIC_RELEVANCE",
    derived_from:"spec/PRODUCT_PAGE_SPEC.json",
    source_spec_sha256:spec.meta.spec_sha256,
    product_context: compactContext(context),
    semantic_contamination: semantic,
    frozen_invariants:{
      story_sequence_fingerprint:spec.story_sequence_lock?.fingerprint || "",
      gallery_ids:spec.product_images.map(item=>item.id),
      aplus_structure:spec.aplus_modules.map(module=>({id:module.id,units:module.units.map(unit=>unit.id)})),
      template_mapping_sha256:hash([...spec.product_images.map(item=>[item.id,item.template_id]),...spec.aplus_modules.map(item=>[item.id,item.template_id])]),
      claims_sha256:hash(spec.claims),
      reference_selection_sha256:hash(spec.reference_selection),
    },
    rules:{
      product_layer:"Official/verified/approved only; AI product generation is prohibited.",
      scene_layer:"AI/stock/photo may supply environment, background and non-product props only.",
      graphic_layer:"All Japanese, UI, comparison, technical labels and arrows are programmatic.",
      story:"Frozen; Art Direction cannot reorder, add, delete, merge or split Gallery/A+ records.",
      primitive:"Frozen; no Primitive additions, deletions or template remapping.",
    },
    product_scale_strategy:{gallery:gallery.map(r=>`${r.id}:${r.product_scale}`),aplus_units:unitRecords.map(r=>`${r.id}:${r.product_scale}`),warnings:scaleWarnings},
    camera_rhythm:{gallery:gallery.map(r=>`${r.id}:${r.camera_angle}`),aplus_units:unitRecords.map(r=>`${r.id}:${r.camera_angle}`),warnings:cameraWarnings},
    lighting_rhythm:{gallery:gallery.map(r=>`${r.id}:${r.lighting}`),aplus_units:unitRecords.map(r=>`${r.id}:${r.lighting}`)},
    production_method_distribution:methodCounts,
    gallery,
    aplus_modules:aplus,
    asset_requirements:assets,
    p0_asset_gaps:assets.filter(asset=>asset.priority==="P0"&&asset.status!=="READY").map(asset=>asset.asset_id),
    p1_asset_gaps:assets.filter(asset=>asset.priority==="P1"&&asset.status!=="READY").map(asset=>asset.asset_id),
    p2_asset_gaps:assets.filter(asset=>asset.priority==="P2"&&asset.status!=="READY").map(asset=>asset.asset_id),
    quality:{
      score,
      score_scope:"Semantic metadata check only; aesthetic dimensions and overall quality are NOT_ASSESSED",
      semantic_relevance:{score:semantic.status === "PASS" ? 100 : 0,status:semantic.status,hard_gate:true},
      jp_lifestyle_fit:{score:null,status:"NOT_ASSESSED",issues:[]},
      current_baseline_score:null,
      recommended_art_direction_score:null,
      human_review_required:true,
    },
    validation:{required_fields:REQUIRED_FIELDS,record_count:gallery.length+unitRecords.length,gallery_count:gallery.length,aplus_module_count:aplus.length,aplus_unit_count:unitRecords.length,new_primitive_count:0,new_reference_count:0,new_gate_count:0},
  };
}

function esc(value){return String(value??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");}
function table(headers,rows){return [`| ${headers.join(" | ")} |`,`| ${headers.map(()=>"---").join(" | ")} |`,...rows.map(row=>`| ${row.map(v=>String(v??"").replaceAll("|","\\|").replaceAll("\n","<br>")).join(" | ")} |`)].join("\n");}

function conceptDiagram(record){
  const tech=/TECHNICAL|3D_RENDER/.test(record.production_method);
  const scene=/SCENE|PHOTOGRAPHY|MIXED/.test(record.production_method);
  return `<div class="concept ${tech?"technical":scene?"scene":"product"}"><div class="negative">COPY / NEGATIVE SPACE</div><div class="hero">${esc(record.hero_object)}</div><div class="secondary">${esc(record.secondary_object)}</div><div class="axis">${esc(record.camera_angle)} · ${esc(record.product_scale)}</div></div>`;
}

function humanFields(id){return `<div class="human"><label>Human Override <select data-review="${id}-override"><option>None</option><option>Accept</option><option>Revise</option></select></label><label>Decision <select data-review="${id}-decision"><option>Pending</option><option>Accept</option><option>Revise</option></select></label><label>Human Comment <textarea data-review="${id}-comment" placeholder="Review note"></textarea></label></div>`;}

function galleryCard(record){
  const seq=String(record.sequence).padStart(2,"0");
  return `<article class="card" id="${record.id}"><header><div><span class="eyebrow">GALLERY ${seq} · ${esc(record.visual_role)}</span><h2>${esc(record.id)} · ${esc(record.frozen_headline||record.story_role)}</h2></div><span class="method">${esc(record.production_method)}</span></header><div class="triptych"><figure><img src="../design/svg/wireframes/product_images/image_${seq}.svg"><figcaption>Wireframe</figcaption></figure><figure><img src="../design/product_images/image_${seq}.jpg"><figcaption>Current Art Direction</figcaption></figure><figure>${conceptDiagram(record)}<figcaption>Recommended Art Direction</figcaption></figure></div><div class="facts"><p><b>Visual Objective</b>${esc(record.visual_objective)}</p><p><b>Consumer Takeaway</b>${esc(record.consumer_takeaway)}</p><p><b>Composition</b>${esc(record.composition)}</p><p><b>Camera / Scale / Light</b>${esc(record.camera_angle)} · ${esc(record.product_scale)} · ${esc(record.lighting)}</p><p><b>Required Assets</b>${esc(record.asset_ids.join(", "))}</p><p><b>Mobile Crop</b>${esc(record.mobile_crop)}</p><p class="risk"><b>Risk / Fallback</b>${esc(record.risk)} / ${esc(record.fallback)}</p></div>${humanFields(record.id)}</article>`;
}

function moduleCard(module){
  const seq=String(module.sequence).padStart(2,"0");
  return `<article class="card" id="${module.id}"><header><div><span class="eyebrow">A+ ${seq} · ${esc(module.visual_role)}</span><h2>${esc(module.id)} · ${esc(module.story_role)}</h2></div><span class="method">${esc(module.production_methods.join(" + "))}</span></header><div class="triptych"><figure><img src="../design/svg/wireframes/aplus/aplus_${seq}.svg"><figcaption>Wireframe</figcaption></figure><figure><img src="../design/aplus/aplus_${seq}.jpg"><figcaption>Current Art Direction</figcaption></figure><figure>${conceptDiagram(module.units[0])}<figcaption>Recommended Art Direction</figcaption></figure></div><div class="module-note"><b>Module Direction</b>${esc(module.recommended_art_direction)}<br><span>${esc(module.pilot_note)}</span></div><div class="units">${module.units.map(unit=>`<section><h3>${esc(unit.id)} · ${esc(unit.frozen_headline)}</h3><p><b>Objective</b>${esc(unit.visual_objective)}</p><p><b>Hero</b>${esc(unit.hero_object)}</p><p><b>Camera</b>${esc(unit.camera_angle)} · ${esc(unit.product_scale)}</p><p><b>Method</b>${esc(unit.production_method)} — ${esc(unit.production_method_reason)}</p><p><b>Assets</b>${esc(unit.asset_ids.join(", "))}</p><p><b>Mobile</b>${esc(unit.mobile_crop)}</p><p class="risk"><b>Risk</b>${esc(unit.risk)}</p></section>`).join("")}</div>${humanFields(module.id)}</article>`;
}

function contactSheet(spec, art){
  const body=`<nav><a href="#gallery">Gallery</a><a href="#aplus">A+</a><a href="#score">Score</a><span>Spec ${esc(art.source_spec_sha256.slice(0,12))}</span></nav><main><section class="hero"><span>ART DIRECTION CONTACT SHEET</span><h1>${esc(spec.product.name)}<br>Production Brief</h1><p>Story / Claim / Reference / Visual Role / Primitive frozen. Placeholder is review-only.</p><div class="kpis"><div><b>${art.validation.record_count}</b>visual units</div><div><b>${art.p0_asset_gaps.length}</b>P0 gaps</div><div><b>未评估</b>成图质量</div><div><b>未评估</b>JP fit</div></div></section><section id="gallery"><h1>Gallery · Decision Acceleration</h1>${art.gallery.map(galleryCard).join("")}</section><section id="aplus"><h1>A+ · Understanding / Trust / Ownership</h1>${art.aplus_modules.map(moduleCard).join("")}</section><section class="score" id="score"><h1>Art Direction Quality</h1>${Object.entries(art.quality.score).map(([k,v])=>`<div><span>${esc(k.replaceAll("_"," "))}</span>${v === null ? "<span>NOT_ASSESSED</span><b>—</b>" : `<meter min="0" max="100" value="${v}"></meter><b>${v}</b>`}</div>`).join("")}<p>语义分仅来自元数据检查；Brief 的构图、真实感与品牌效果必须在实际成图后评估。</p></section></main>`;
  const css=`:root{--ink:#17212b;--muted:#5f6d73;--mint:#23a98f;--paper:#fff;--canvas:#edf3f1;--risk:#9a3412}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--canvas);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP","Microsoft YaHei",sans-serif}nav{position:sticky;top:0;z-index:9;display:flex;gap:18px;align-items:center;padding:14px 4vw;background:#142621;color:#fff}nav a{color:#fff;text-decoration:none}nav span{margin-left:auto;color:#bfe9de}main{max-width:1500px;margin:auto;padding:36px}.hero{padding:72px;background:#173c35;color:#fff;border-radius:0 0 48px 0}.hero>span,.eyebrow{letter-spacing:.14em;color:#64d6bd;font-weight:800;font-size:12px}.hero h1{font-size:clamp(38px,6vw,84px);line-height:1.02;margin:16px 0 22px}.hero p{max-width:760px;color:#d7e5e1}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:42px;background:#46635c}.kpis div{background:#173c35;padding:20px}.kpis b{display:block;font-size:34px;color:#64d6bd}section>h1{font-size:34px;margin:72px 0 24px}.card{background:#fff;margin:0 0 28px;padding:28px;border-radius:3px;box-shadow:0 12px 30px #153b3112}.card header{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.card h2{margin:8px 0 20px;font-size:27px}.method{background:#e5f6f1;color:#145b4e;padding:8px 12px;font-size:12px;font-weight:800}.triptych{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.triptych figure{margin:0;background:#f6f8f7;border:1px solid #dfe7e4}.triptych img,.concept{display:block;width:100%;aspect-ratio:16/9;object-fit:contain;background:#f4f7f6}.triptych figcaption{padding:10px 12px;color:var(--muted);font-size:12px}.concept{position:relative;overflow:hidden;background:linear-gradient(135deg,#f8fbfa,#deeee9)}.concept.scene{background:linear-gradient(150deg,#eee7de,#faf8f3)}.concept.technical{background:#edf7f6}.concept>div{position:absolute}.concept .negative{top:10%;left:6%;width:35%;height:28%;border:1px dashed #77a79b;padding:8px;font-size:11px;color:#52716a}.concept .hero{right:8%;bottom:12%;width:48%;height:62%;display:flex;align-items:center;justify-content:center;padding:15px;background:#fff;border-radius:50% 50% 35% 35%;color:#375b53;font-size:12px;text-align:center}.concept .secondary{left:8%;bottom:13%;width:34%;padding:10px;background:#d7ebe5;font-size:11px}.concept .axis{right:4%;top:4%;font-size:10px;color:#4b6c65}.facts{display:grid;grid-template-columns:repeat(2,1fr);gap:10px 24px;margin-top:20px}.facts p,.units p{margin:0;color:var(--muted);line-height:1.55}.facts b,.units b,.module-note b{display:block;color:var(--ink);font-size:12px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px}.risk{color:var(--risk)!important}.module-note{padding:18px 0;border-bottom:2px solid #d8e6e2;line-height:1.6}.module-note span{color:var(--muted)}.units{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#dfe7e4;margin-top:18px}.units section{background:#fff;padding:18px}.units h3{margin:0 0 12px;font-size:17px}.units p{margin-bottom:9px}.human{display:grid;grid-template-columns:180px 180px 1fr;gap:12px;margin-top:22px;padding-top:18px;border-top:1px solid #e2e8e6}.human label{font-size:12px;color:var(--muted)}select,textarea{display:block;width:100%;margin-top:5px;border:1px solid #b8c5c1;padding:9px;background:#fff}textarea{min-height:58px}.score{background:#fff;padding:30px;margin-top:50px}.score>div{display:grid;grid-template-columns:220px 1fr 50px;gap:15px;margin:12px 0}.score meter{width:100%;height:16px}@media(max-width:700px){nav{overflow:auto}main{padding:12px}.hero{padding:42px 22px}.kpis{grid-template-columns:1fr 1fr}.card{padding:16px}.card header{display:block}.triptych{grid-template-columns:1fr}.facts,.units,.human{grid-template-columns:1fr}.facts p,.units p,.module-note,.human label{font-size:14px}.score>div{grid-template-columns:130px 1fr 34px}.card h2{font-size:22px}}`;
  const script=`const key='art-direction-review-v1';let saved={};try{saved=JSON.parse(localStorage.getItem(key)||'{}')}catch{}document.querySelectorAll('[data-review]').forEach(el=>{if(saved[el.dataset.review]!=null)el.value=saved[el.dataset.review];el.addEventListener('input',()=>{saved[el.dataset.review]=el.value;localStorage.setItem(key,JSON.stringify(saved))})});`;
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Art Direction Contact Sheet</title><style>${css}</style></head><body>${body}<script>${script}</script></body></html>`;
}

export async function writeArtDirectionArtifacts(spec, art, outputDir) {
  await Promise.all(["spec","review","reports","qa"].map(dir=>fs.mkdir(path.join(outputDir,dir),{recursive:true})));
  const context = buildProductSemanticContext(spec);
  await fs.writeFile(path.join(outputDir,"spec","ART_DIRECTION_SPEC.json"),`${JSON.stringify(art,null,2)}\n`,"utf8");
  await fs.writeFile(path.join(outputDir,"spec","PRODUCT_SEMANTIC_CONTEXT.json"),`${JSON.stringify(context,null,2)}\n`,"utf8");
  await fs.writeFile(path.join(outputDir,"review","ART_DIRECTION_CONTACT_SHEET.html"),contactSheet(spec,art),"utf8");
  await fs.writeFile(path.join(outputDir,"reports","ART_DIRECTION_SCORE.json"),`${JSON.stringify(art.quality,null,2)}\n`,"utf8");
  await fs.writeFile(path.join(outputDir,"qa","semantic-contamination.json"),`${JSON.stringify(art.semantic_contamination,null,2)}\n`,"utf8");
  const system=`# Art Direction System\n\n## Boundary\n\nArt Direction is a derived layer under PRODUCT_PAGE_SPEC. It may define shot, render, scene, crop, light and production method; it may not change Story, Claims, Reference, Visual Role, template_id, Primitive, module/unit count or Gates.\n\n## Three layers\n\n- Product Layer: approved official asset only; AI product generation is prohibited.\n- Scene Layer: licensed photo or AI environment without product/logo/text/UI.\n- Graphic Layer: programmatic Japanese, technical labels, arrows, UI and comparison.\n\n## Production methods\n\n${PRODUCTION_METHODS.map(x=>`- \`${x}\``).join("\n")}\n\n## Required record fields\n\n${REQUIRED_FIELDS.map(x=>`- \`${x}\``).join("\n")}\n\n## Rhythm\n\nCamera, scale and lighting are selected by Visual Objective. Three consecutive identical camera or scale decisions create a review warning; random variation is prohibited.\n`;
  await fs.writeFile(path.join(outputDir,"ART_DIRECTION_SYSTEM.md"),system,"utf8");
  const assets=table(["Asset ID","Priority","Purpose","Shot / Render","Angle","Resolution","State","Claim","Owner","Status","Fallback"],art.asset_requirements.map(a=>[a.asset_id,a.priority,a.purpose,a.shot_render_type,a.angle,a.resolution,a.required_product_state,a.claim_dependency,a.owner,a.status,a.fallback]));
  await fs.writeFile(path.join(outputDir,"ASSET_PRODUCTION_PRIORITY.md"),`# Asset Production Priority\n\n- P0: ${art.p0_asset_gaps.length}\n- P1: ${art.p1_asset_gaps.length}\n- P2: ${art.p2_asset_gaps.length}\n- Product Layer assets must be official/verified/approved.\n- No P2 asset is added when the enhancement is non-essential and a safe fallback already exists.\n\n${assets}\n`,"utf8");
  await fs.writeFile(path.join(outputDir,"SMART_LOCK_SEMANTIC_CONTEXT.md"),`# Smart Lock Semantic Context\n\n- Product: ${spec.product.name}\n- Category: ${context.category_name}\n- Context SHA-256: \`${context.context_sha256}\`\n- Semantic relevance: **${art.semantic_contamination.status}**\n\n## Purchase truth hierarchy\n\n1. Product identity and exact SKU\n2. Door and thumbturn fit\n3. Installation state and sequence\n4. Lock-body versus accessory capability ownership\n5. Power, communication and physical-key exception handling\n6. Configuration and support closure\n\n## Hard boundary\n\nArt Direction is evaluated only against the current product context. Cross-product terms are blocked by \`category-semantics/smart-lock.json\`; a match is a P0 failure. Product body imagery remains official-only.\n`,"utf8");
  await fs.writeFile(path.join(outputDir,"JP_LIFESTYLE_ART_DIRECTION.md"),`# JP Lifestyle Art Direction\n\nJP_LIFESTYLE_FIT: **${art.quality.jp_lifestyle_fit.status} — inspect actual output before rating**\n\n- Home type: credible Japanese apartment entryway.\n- Door relationship: installed-side geometry must match an approved product state.\n- Human action: restrained and used only to explain an entry or installation task.\n- Product Layer: official-only and composited after scene production.\n- Avoid: luxury staging, crowded props, generated product body, unsupported capability cues and inaccurate installation geometry.\n`,"utf8");
  await fs.writeFile(path.join(outputDir,"TECHNICAL_VISUALIZATION_GUIDE.md"),`# Technical Visualization Guide\n\n- Compatibility: measured door, thumbturn and clearance relationships only.\n- Installation: approved order and real product state.\n- Capability ownership: lock body, accessory, app and hub are separate layers.\n- Exception handling: verified power, communication and physical-key relationships; no absolute promise.\n- Configuration: official exact-SKU packshots plus a programmatic table.\n- All Japanese labels, arrows, conditions, comparison and UI are programmatic Graphic Layer.\n`,"utf8");
  const constraints=table(["Location","Constraint","Impact","Action"],[
    ["Compatibility proof","Current measurements and fit rules are not approved.","The diagram cannot show definitive thresholds.","Keep conditions explicit and request Engineering-approved geometry."],
    ["Capability comparison","The sales-set and accessory relationship are pending.","A configuration table can misattribute capability or inclusion.","Use exact-SKU official assets and approved capability ownership only."],
    ["390px A+","Every Unit must retain headline, body, condition and annotation.","Text cannot be hidden for visual simplification.","Apply the unified mobile content contract."],
  ]);
  await fs.writeFile(path.join(outputDir,"ART_DIRECTION_LAYOUT_CONSTRAINTS.md"),`# Art Direction Layout Constraints\n\nNo Primitive was added, removed or remapped.\n\n${constraints}\n`,"utf8");
  const regression=`# Art Direction Regression\n\n## Verdict\n\n**${art.semantic_contamination.status === "PASS" ? "ART_DIRECTION_READY" : "BLOCKED"}** for ${spec.product.name} asset-production briefing. This does not mean the PDP is publish-ready.\n\n- Semantic relevance: ${art.quality.semantic_relevance.status}\n- Cross-product contamination: ${art.semantic_contamination.hit_count}\n- Gallery: ${art.validation.gallery_count}\n- A+ Modules / Units: ${art.validation.aplus_module_count} / ${art.validation.aplus_unit_count}\n- New Primitive / Reference / Gate: 0 / 0 / 0\n- P0 / P1 gaps: ${art.p0_asset_gaps.length} / ${art.p1_asset_gaps.length}\n`;
  await fs.writeFile(path.join(outputDir,"ART_DIRECTION_REGRESSION.md"),regression,"utf8");
}

export function validateArtDirectionSpec(art) {
  const unitRecords=[...art.gallery,...art.aplus_modules.flatMap(module=>module.units)];
  const missing=[];
  for(const record of unitRecords) for(const field of REQUIRED_FIELDS) if(record[field]===undefined||record[field]===null||record[field]==="") missing.push(`${record.id}.${field}`);
  const invalidMethods=unitRecords.filter(record=>!PRODUCTION_METHODS.includes(record.production_method)).map(record=>record.id);
  const unsafeAi=unitRecords.filter(record=>record.production_method==="AI_SCENE_ONLY"&&!/no product|without product|product is added from official/i.test(`${record.scene_layer_rule} ${record.production_method_reason}`)).map(record=>record.id);
  const checkContext = buildProductSemanticContext({ product: art.product_context?.product || {} });
  const semantic = scanSemanticContamination({gallery:art.gallery,aplus_modules:art.aplus_modules,asset_requirements:art.asset_requirements},checkContext);
  const semanticFailures=unitRecords.filter(record=>record.semantic_relevance?.status!=="PASS").map(record=>record.id);
  const failed=missing.length||invalidMethods.length||unsafeAi.length||semantic.status!=="PASS"||semanticFailures.length;
  return {status:failed?"FAIL":"PASS",record_count:unitRecords.length,missing_fields:missing,invalid_methods:invalidMethods,unsafe_ai_scene_records:unsafeAi,semantic_relevance:semantic,semantic_relevance_failures:semanticFailures};
}
