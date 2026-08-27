#!/usr/bin/env python3
"""Render a concise Chinese Visual Review from visual-profile.yaml.

This is a review artifact, not an EDM renderer and not a production approval.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML object: {path}")
    return value


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else "—"))


def status_class(value: str) -> str:
    normalized = str(value).lower()
    if "ready" in normalized and "not" not in normalized:
        return "ok"
    if "blocked" in normalized or "low" in normalized:
        return "bad"
    return "warn"


def metric_card(label: str, metric: dict[str, Any]) -> str:
    score = float(metric.get("score", 0))
    status = metric.get("status", "UNKNOWN")
    return f"""
      <article class="metric">
        <div class="metric__top"><span>{esc(label)}</span><strong>{score:.1f}</strong></div>
        <div class="bar"><span style="width:{max(0, min(100, score)):.1f}%"></span></div>
        <span class="badge {status_class(status)}">{esc(status)}</span>
      </article>
    """.strip()


def list_items(items: list[Any], empty: str = "无") -> str:
    if not items:
        return f"<li>{esc(empty)}</li>"
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def channel_card(channel: str, assignment: dict[str, Any]) -> str:
    pattern = assignment.get("primary_pattern", {})
    recipe = assignment.get("recipe", {})
    readiness = assignment.get("execution_readiness", {})
    match = assignment.get("pattern_match", {})
    confidence = assignment.get("evidence_confidence", {})
    template = assignment.get("adapter", {}).get("existing_template") or {}
    template_id = template.get("template_id", "Existing Amazon Flow") if isinstance(template, dict) else template
    return f"""
      <article class="assignment">
        <div class="assignment__head">
          <div><span class="eyebrow">{esc(channel.upper())}</span><h3>{esc(pattern.get('pattern_id'))}</h3></div>
          <span class="badge {status_class(readiness.get('status', ''))}">{esc(readiness.get('status'))}</span>
        </div>
        <dl>
          <div><dt>Pattern 状态</dt><dd>{esc(pattern.get('status'))}</dd></div>
          <div><dt>Recipe</dt><dd>{esc(recipe.get('recipe_id'))} · {esc(recipe.get('status'))}</dd></div>
          <div><dt>既有 Template</dt><dd>{esc(template_id)}</dd></div>
          <div><dt>Match / Readiness / Confidence</dt><dd>{esc(match.get('score'))} / {esc(readiness.get('score'))} / {esc(confidence.get('score'))}</dd></div>
          <div><dt>Auto Apply</dt><dd>{esc(assignment.get('auto_apply', {}).get('status'))}</dd></div>
          <div><dt>完整 Layout 跨渠道继承</dt><dd>{'否' if not assignment.get('inheritance', {}).get('layout_from_other_channel') else '是'}</dd></div>
        </dl>
      </article>
    """.strip()


def render(profile: dict[str, Any]) -> str:
    dna = profile["project_visual_dna"]
    assignments = profile["channel_assignments"]
    amazon = assignments.get("amazon_jp", {})
    edm = assignments.get("edm", {})
    freeze = edm.get("freeze", {})
    edm_sections = edm.get("recipe", {}).get("section_patterns", [])
    wireframe_labels = {
        "SEC-EDM-PRODUCT-FIRST-HERO": "产品优先 Hero",
        "SEC-EDM-CONSUMER-PROBLEM": "消费者问题",
        "SEC-EDM-BENEFIT-SUMMARY": "利益概览",
        "SEC-EDM-MECHANISM-PROOF": "机制证据",
        "SEC-EDM-APP-AUTOMATION": "App / 自动化",
        "SEC-EDM-CHANNEL-CTA": "购买 CTA",
    }
    wireframe = "".join(
        f'<div class="wire wire--{index % 3}"><span>{index:02d}</span><strong>{esc(wireframe_labels.get(section, section))}</strong><small>结构候选 · 内容待 Gate</small></div>'
        for index, section in enumerate(edm_sections, 1)
    )
    dna_rows = "".join(
        f"<div><dt>{esc(label)}</dt><dd>{esc(' / '.join(value) if isinstance(value, list) else value)}</dd></div>"
        for label, value in [
            ("状态", dna.get("status")),
            ("Tone", dna.get("tone", [])),
            ("Proof Strategy", dna.get("proof_strategy")),
            ("Visual Rhythm", dna.get("visual_rhythm")),
            ("Image Strategy", dna.get("image_strategy")),
            ("Information Density", dna.get("information_density")),
            ("Conversion Style", dna.get("conversion_style")),
            ("Mobile Priority", dna.get("mobile_priority")),
        ]
    )
    freeze_notes = freeze.get("notes", [])
    blockers = edm.get("blocking_reasons", [])
    reason_codes = edm.get("reason_codes", [])
    project_id = profile.get("project_id")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="icon" href="data:,">
  <title>{esc(project_id)} Visual Review</title>
  <style>
    :root{{--red:#e63223;--ink:#171717;--muted:#696969;--line:#e9e5df;--paper:#fff;--cream:#f7f4ef;--dark:#241f1c}}
    *{{box-sizing:border-box}} body{{margin:0;background:var(--cream);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif}}
    .shell{{max-width:1180px;margin:auto;padding:36px 24px 72px}} .hero{{background:var(--dark);color:#fff;border-radius:28px;padding:36px;display:grid;grid-template-columns:1.4fr .8fr;gap:30px;box-shadow:0 20px 50px #362b221c}}
    .eyebrow{{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#e9594d}} h1{{font-size:clamp(34px,5vw,62px);line-height:1.02;margin:12px 0 16px;max-width:760px}} .hero p{{color:#d8d1cb;max-width:680px}}
    .gate{{border:1px solid #ffffff2d;border-radius:20px;padding:22px;background:#ffffff0b}} .gate strong{{display:block;font-size:25px;margin:8px 0}} .gate small{{color:#c7beb6}}
    section{{margin-top:34px}} .section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:14px}} h2{{font-size:26px;margin:0}} .section-head p{{margin:0;color:var(--muted)}}
    .metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .metric,.assignment,.panel{{background:var(--paper);border:1px solid var(--line);border-radius:20px;padding:20px}}
    .metric__top{{display:flex;justify-content:space-between;align-items:center}} .metric__top strong{{font-size:28px}} .bar{{height:8px;background:#eeeae4;border-radius:999px;overflow:hidden;margin:12px 0}} .bar span{{display:block;height:100%;background:linear-gradient(90deg,#f09b74,var(--red))}}
    .badge{{display:inline-flex;padding:5px 9px;border-radius:999px;font-size:11px;font-weight:800;letter-spacing:.04em;background:#f2eee9}} .badge.bad{{background:#ffe7e4;color:#a7261d}} .badge.warn{{background:#fff0cf;color:#8a5d00}} .badge.ok{{background:#dff5e8;color:#12673a}}
    .assignments{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} .assignment__head{{display:flex;justify-content:space-between;gap:12px;align-items:start}} h3{{margin:4px 0 14px;font-size:19px}} dl{{margin:0}} dl div{{display:grid;grid-template-columns:170px 1fr;gap:14px;padding:10px 0;border-top:1px solid var(--line)}} dt{{color:var(--muted)}} dd{{margin:0;font-weight:650;word-break:break-word}}
    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} ul{{margin:8px 0 0;padding-left:20px}} .reason-codes{{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}} .code{{padding:5px 8px;background:#f5f1ec;border-radius:8px;font:11px/1.3 ui-monospace,SFMono-Regular,Menlo,monospace}}
    .inherit{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .inherit .panel:first-child{{border-top:4px solid #2e9b61}} .inherit .panel:last-child{{border-top:4px solid var(--red)}}
    .phone-wrap{{display:grid;grid-template-columns:320px 1fr;gap:28px;align-items:center}} .phone{{width:286px;margin:auto;background:#111;border:9px solid #111;border-radius:40px;padding:14px 10px 22px;box-shadow:0 24px 45px #2b211b2d}} .phone__screen{{background:#f7f5f2;border-radius:25px;padding:12px;min-height:570px}} .phone__notch{{width:90px;height:18px;background:#111;border-radius:0 0 13px 13px;margin:-12px auto 14px}}
    .wire{{background:#fff;border:1px solid #e5dfd7;border-radius:13px;padding:13px;margin:9px 0;min-height:58px}} .wire--1{{min-height:92px;background:linear-gradient(145deg,#fff4f1,#fff)}} .wire--2{{background:#f2f1ef}} .wire span{{font-size:10px;color:var(--red);font-weight:800;margin-right:7px}} .wire strong{{font-size:12px}} .wire small{{display:block;color:#8a837c;font-size:10px;margin-top:4px}}
    .callout{{background:#fff0ed;border-left:5px solid var(--red);padding:16px 18px;border-radius:5px 16px 16px 5px}} footer{{margin-top:34px;color:var(--muted);font-size:12px}}
    @media(max-width:800px){{.hero,.metrics,.assignments,.grid,.inherit,.phone-wrap{{grid-template-columns:1fr}} .shell{{padding:18px 14px 44px}} .hero{{padding:24px;border-radius:20px}} dl div{{grid-template-columns:1fr;gap:2px}} .section-head{{display:block}}}}
  </style>
</head>
<body data-project-id="{esc(project_id)}">
  <main class="shell">
    <header class="hero">
      <div><span class="eyebrow">Visual Pattern Memory · Phase 2A Pilot</span><h1>S30 mini<br>Amazon → EDM</h1><p>本页面只审核跨渠道视觉结构。它不包含或批准产品事实、Claim、价格、性能数字、正式素材、Amazon 上传或 EDM 发送。</p></div>
      <aside class="gate"><span class="eyebrow">Recommended Gate</span><strong>HUMAN + ASSET REVIEW</strong><span class="badge bad">AUTO APPLY BLOCKED</span><small>EDM Pattern 与 Recipe 均为 Candidate，且 Product Truth、Claim、素材仍未满足。</small></aside>
    </header>

    <section><div class="section-head"><div><span class="eyebrow">01 · Project Visual DNA</span><h2>跨渠道继承的是视觉原则，不是 Layout</h2></div><p>{esc(dna.get('status'))}</p></div><article class="panel"><dl>{dna_rows}</dl></article></section>

    <section><div class="section-head"><div><span class="eyebrow">02 · Decision Metrics</span><h2>Match 与 Production Readiness 分开判断</h2></div></div><div class="metrics">{metric_card('Amazon Pattern Match', amazon.get('pattern_match', {}))}{metric_card('EDM Execution Readiness', edm.get('execution_readiness', {}))}{metric_card('EDM Evidence Confidence', edm.get('evidence_confidence', {}))}</div></section>

    <section><div class="section-head"><div><span class="eyebrow">03 · Channel Assignments</span><h2>同一个项目 Profile，两个渠道适配</h2></div></div><div class="assignments">{channel_card('amazon_jp', amazon)}{channel_card('edm', edm)}</div></section>

    <section><div class="section-head"><div><span class="eyebrow">04 · Freeze & Gate</span><h2>Candidate Freeze 没有继承到 EDM</h2></div></div><div class="grid"><article class="panel"><h3>原因</h3><ul>{list_items(freeze_notes, '没有 Freeze 记录')}</ul></article><article class="panel"><h3>EDM 素材与事实缺口</h3><ul>{list_items(blockers)}</ul><div class="reason-codes">{''.join(f'<span class="code">{esc(code)}</span>' for code in reason_codes)}</div></article></div></section>

    <section><div class="section-head"><div><span class="eyebrow">05 · Cross-channel Boundary</span><h2>继承项与差异项</h2></div></div><div class="inherit"><article class="panel"><h3>Amazon → EDM 可以继承</h3><ul><li>Tone 与品牌亲和度方向</li><li>Proof Strategy 与信息优先级</li><li>产品优先、机制到证据的 Visual Rhythm</li><li>高信息复杂度下的结构化密度</li><li>Mobile Priority 与单一行动原则</li></ul></article><article class="panel"><h3>必须重新适配</h3><ul><li>Amazon Gallery / A+ Layout 与尺寸</li><li>EDM 600px、语义堆叠与邮件客户端约束</li><li>Template、Module、CTA、Legal 与 Footer</li><li>价格、Coupon、日期、Claim、图片与产品文案</li><li>Mobile QA、Human Review 与 ESP Gate</li></ul></article></div></section>

    <section><div class="section-head"><div><span class="eyebrow">06 · Mobile Wireframe Preview</span><h2>EDM Recipe 的手机端阅读顺序</h2></div><p>结构预览，不是 EDM 成品</p></div><div class="phone-wrap"><div class="phone"><div class="phone__screen"><div class="phone__notch"></div>{wireframe}<div class="wire"><strong>Legal Note / Brand Footer</strong><small>既有 Runtime 负责</small></div></div></div><div><h3>{esc(edm.get('recipe', {}).get('recipe_id'))}</h3><p>映射到既有 <strong>TPL-LAUNCH-A</strong> 和 EDM Module System，但最终 Template Selector、Renderer、Mobile QA 与 ESP Gate 仍归现有 Skill 所有。</p><div class="callout"><strong>Human Review 原因</strong><br>Pattern 和 Recipe 均为 Candidate；S30 Product Truth、Approved Claim、官方产品/机制/UI 素材与 CTA 尚未完成。</div></div></div></section>

    <footer>Generated from repository-relative Visual Profile · Review artifact only · No Product Truth / Claim / Asset / Send approval</footer>
  </main>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a project Visual Review HTML")
    parser.add_argument("--project", required=True, help="Project id or repository-relative project directory")
    parser.add_argument("--output", help="Output file; defaults to projects/<id>/visual-review.html")
    args = parser.parse_args()
    project_dir = Path(args.project)
    if not project_dir.is_absolute():
        candidate = (Path.cwd() / project_dir).resolve()
        project_dir = candidate if candidate.is_dir() else ROOT / "projects" / args.project
    profile = load_yaml(project_dir / "visual-profile.yaml")
    output = Path(args.output).resolve() if args.output else project_dir / "visual-review.html"
    output.write_text(render(profile), encoding="utf-8")
    print(f"WROTE {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
