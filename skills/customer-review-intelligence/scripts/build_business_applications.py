#!/usr/bin/env python3
"""Build traceable VOC business outputs from normalized reviews."""
from __future__ import annotations

import argparse, csv, json, math, re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0]) if rows else ["status"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows or [{"status":"Not Available"}])


def six_sentiment(r):
    rating = float(r["rating"]) if r.get("rating") else None
    core = r.get("sentiment") or "Neutral"
    if core == "Mixed": return "Mixed"
    if core == "Positive" and rating == 5: return "Strong Positive"
    if core == "Negative" and rating is not None and rating <= 2: return "Strong Negative"
    return core


def mismatch(r, six):
    rating = float(r["rating"]) if r.get("rating") else None
    return "Yes" if rating and ((rating >= 4 and six in {"Negative","Strong Negative"}) or (rating <= 2 and six in {"Positive","Strong Positive"})) else "No"


def responsibility(r):
    if r.get("logistics_related") == "Yes": return "Logistics"
    if r.get("app_related") == "Yes": return "App"
    if r.get("firmware_related") == "Yes": return "Firmware"
    if r.get("hardware_related") == "Yes": return "Hardware"
    if r.get("installation_related") == "Yes": return "Installation Environment"
    return r.get("responsibility_owner") or "Undetermined"


def need_type(r, six):
    text=(r.get("review_title","")+" "+r.get("review_body","")).lower()
    if any(x in text for x in ("ほしい","欲しい","追加して","対応して")): return "Feature Request"
    if r.get("expectation_gap"): return "Expectation Gap"
    if "competitor comparison" in (r.get("primary_topic","")+r.get("secondary_topics","" )).lower(): return "Competitor Comparison"
    if r.get("return_intent") == "Yes": return "Churn Risk"
    if six in {"Strong Negative","Negative"}: return "Unmet"
    if six == "Mixed": return "Partially Satisfied"
    return "Satisfied"


def normalize(values):
    top=max(values) if values else 0
    return [0 if top == 0 else round(v/top*100,1) for v in values]


def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); p.add_argument("--source",default="amazon_jp"); p.add_argument("--product",default="ai_art_canvas"); p.add_argument("--batch-id",default=""); args=p.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    rows=[r for r in read_rows(Path(args.input)) if r.get("source")==args.source and r.get("product_id")==args.product and r.get("review_status") in {"Active","Updated"}]
    for r in rows:
        r["business_sentiment"]=six_sentiment(r); r["rating_sentiment_mismatch"]=mismatch(r,r["business_sentiment"]); r["responsibility_type"]=responsibility(r); r["need_type"]=need_type(r,r["business_sentiment"])
    topics=defaultdict(list)
    for r in rows:
        if r["business_sentiment"] in {"Negative","Strong Negative","Mixed"}: topics[r.get("primary_topic") or "Other"].append(r)
    names=list(topics); freq=[len(topics[x]) for x in names]; freq_n=normalize(freq)
    issue_rows=[]
    for i,name in enumerate(names):
        group=topics[name]; ratings=[float(r["rating"]) for r in group if r.get("rating")]; strong=sum(r["business_sentiment"]=="Strong Negative" for r in group)
        intensity=round((strong*100+sum(r["business_sentiment"]=="Negative" for r in group)*70+sum(r["business_sentiment"]=="Mixed" for r in group)*45)/len(group),1)
        rating_impact=round(max(0,(5-(sum(ratings)/len(ratings) if ratings else 3))/4*100),1)
        helpful=[int(r["helpful_votes"]) for r in group if str(r.get("helpful_votes","")).isdigit()]; helpful_score=round(min(100,sum(helpful)*10),1) if helpful else None
        dates=[r.get("review_date","") for r in group if re.fullmatch(r"\d{4}-\d{2}-\d{2}",r.get("review_date",""))]; recent=sum(d>="2026-05-01" for d in dates); recency=round(recent/len(dates)*100,1) if dates else None
        weights=[(.25,freq_n[i]),(.20,intensity),(.15,rating_impact),(.10,helpful_score),(.15,recency),(.15,100)]
        available=[(w,v) for w,v in weights if v is not None]; score=round(sum(w*v for w,v in available)/sum(w for w,v in available),1)
        severe=any(r.get("severity") in {"Critical","High"} for r in group)
        priority="P0" if any(r.get("severity")=="Critical" for r in group) else "P1" if score>=70 or (severe and len(group)>=2) else "P2" if score>=40 and len(group)>=2 else "P3" if len(group)>=2 else "Monitor"
        conf="High" if len(group)>=5 else "Medium" if len(group)>=2 else "Low"
        topic_owner={"Display Quality":"Hardware / Product","Content Capacity":"App","Installation":"Product / Content"}.get(name)
        issue_rows.append({"product":args.product,"issue":name,"occurrences":len(group),"share_of_amazon_reviews":round(len(group)/len(rows),4) if rows else 0,"average_rating":round(sum(ratings)/len(ratings),2) if ratings else "","strong_negative":strong,"helpful_votes":sum(helpful) if helpful else "Not Available","frequency_score":freq_n[i],"negative_intensity_score":intensity,"rating_impact_score":rating_impact,"helpfulness_score":helpful_score if helpful_score is not None else "Not Available","recency_score":recency if recency is not None else "Not Available","product_importance_score":100,"priority_score":score,"priority":priority,"confidence":conf,"responsibility":topic_owner or Counter(r["responsibility_type"] for r in group).most_common(1)[0][0],"root_cause":"[Hypothesis] Requires product telemetry, return reasons or reproduction","evidence_review_ids":"; ".join(r["review_id"] for r in group[:8])})
    issue_rows.sort(key=lambda x:(x["priority_score"],x["occurrences"]),reverse=True)
    voice=[]
    for r in rows:
        voice.append({"product":args.product,"platform":args.source,"rating":r.get("rating"),"review_date":r.get("review_date"),"original_japanese":r.get("review_body"),"chinese_summary":r.get("review_title") or "保留日文原文，中文摘要待人工复核","sentiment":r["business_sentiment"],"primary_topic":r.get("primary_topic"),"secondary_topics":r.get("secondary_topics"),"usage_scenario":r.get("usage_scenario"),"need_type":r["need_type"],"responsibility":r["responsibility_type"],"rating_sentiment_mismatch":r["rating_sentiment_mismatch"],"marketing_quote_candidate":"Internal only" if r["business_sentiment"] in {"Positive","Strong Positive","Mixed"} else "No","authorization_required":"Yes","review_id":r.get("review_id"),"source_url":r.get("review_url"),"coverage_status":r.get("coverage_status")})
    write_csv(out/"customer_voice_library.csv",voice); write_csv(out/"issue_priority.csv",issue_rows)
    product_backlog=[]; support=[]; actions=[]
    for x in issue_rows:
        if x["priority"]=="Monitor": continue
        product_backlog.append({"product":args.product,"issue":x["issue"],"occurrences":x["occurrences"],"average_rating":x["average_rating"],"priority_score":x["priority_score"],"priority":x["priority"],"confidence":x["confidence"],"possible_root_cause":x["root_cause"],"recommended_action":f"Reproduce and define acceptance criteria for {x['issue']}","owner_suggestion":x["responsibility"],"acceptance_metric":"Root cause recorded; fix or documented limitation validated","evidence_review_ids":x["evidence_review_ids"]})
        actions.append({"Action":f"Investigate and address {x['issue']}","Department":x["responsibility"],"Product":args.product,"Evidence":x["evidence_review_ids"],"Expected Impact":"Reduce negative experience and expectation gap","Owner Suggestion":x["responsibility"],"Deadline":"Next biweekly review","Priority":x["priority"],"KPI":"Issue recurrence and negative rate","Status":"Not Started"})
        if x["responsibility"] in {"App","Installation Environment","Marketing","Customer Support","EC"}:
            support.append({"issue":x["issue"],"product":args.product,"review_count":x["occurrences"],"recommended_resolution":"FAQ, setup guide, in-app guidance or support script after factual validation","content_format":"FAQ + short Japanese tutorial","suggested_title":f"{x['issue']} の確認方法と対処手順","priority":x["priority"],"owner_suggestion":"Customer Support / Content","acceptance_metric":"Self-serve resolution rate; repeat-contact rate","evidence_review_ids":x["evidence_review_ids"]})
    positives=Counter(r.get("primary_topic") or "Other" for r in rows if r["business_sentiment"] in {"Positive","Strong Positive","Mixed"})
    marketing=[]
    for topic,count in positives.most_common(10):
        group=[r for r in rows if (r.get("primary_topic") or "Other")==topic and r["business_sentiment"] in {"Positive","Strong Positive","Mixed"}]
        marketing.append({"product":args.product,"recognized_value":topic,"evidence_count":count,"sample_size":len(rows),"usage_scenarios":"; ".join(sorted({r.get('usage_scenario','') for r in group if r.get('usage_scenario')})) or "Not Available","recommended_message_direction":f"Demonstrate {topic} with real use scenes","recommended_channels":"LP / EC / EDM / PR / KOL","avoid_expression":"Do not generalize beyond the observed Amazon sample","evidence_strength":"High" if count>=5 else "Medium" if count>=2 else "Low","suggested_test":"A/B test evidence-led scene vs feature-led message","evidence_review_ids":"; ".join(r["review_id"] for r in group[:8])})
    write_csv(out/"product_improvement_backlog.csv",product_backlog); write_csv(out/"marketing_insight_playbook.csv",marketing); write_csv(out/"support_content_backlog.csv",support); write_csv(out/"voc_action_plan.csv",actions)
    competitor=[{"product":args.product,"competitor":re.search(r"WaveShare|Aura|InkPoster|The Frame",r.get("review_body","") or "",re.I).group(0),"comparison_dimension":r.get("primary_topic"),"user_voice":r.get("review_body"),"review_id":r.get("review_id"),"source_url":r.get("review_url")} for r in rows if re.search(r"WaveShare|Aura|InkPoster|The Frame",r.get("review_body","") or "",re.I)]
    write_csv(out/"competitor_mentions.csv",competitor)
    sent=Counter(r["business_sentiment"] for r in rows); ratings=[float(r["rating"]) for r in rows if r.get("rating")]
    data={"meta":{"product":args.product,"source":args.source,"batch_id":args.batch_id,"generated_at":datetime.now().isoformat(timespec="seconds"),"coverage_status":"Partial","coverage_note":"73 of 90 displayed Amazon text reviews are auditable; inaccessible remainder is not zero."},"kpis":{"reviews":len(rows),"average_rating":round(sum(ratings)/len(ratings),2) if ratings else None,"positive_rate":round(sum(sent[x] for x in ("Positive","Strong Positive"))/len(rows),4) if rows else None,"negative_rate":round(sum(sent[x] for x in ("Negative","Strong Negative"))/len(rows),4) if rows else None,"strong_negative":sent["Strong Negative"],"mismatches":sum(r["rating_sentiment_mismatch"]=="Yes" for r in rows),"p0_p1":sum(x["priority"] in {"P0","P1"} for x in issue_rows)},"sentiment":sent,"ratings":Counter(r.get("rating") or "Unknown" for r in rows),"issues":issue_rows,"voices":voice}
    (out/"dashboard_data.json").write_text(json.dumps(data,ensure_ascii=False,indent=2,default=dict),encoding="utf-8")
    top_pos=", ".join(f"{k} ({v})" for k,v in positives.most_common(5)) or "Not Available"; top_neg=", ".join(f"{x['issue']} ({x['occurrences']})" for x in issue_rows[:5]) or "Not Available"
    (out/"latest_update_summary.md").write_text(f"# Latest Update Summary\n\n- [Fact] Amazon Japan 可审计评论：{len(rows)} / 页面显示 90，状态 Partial。\n- [Fact] 六级情绪：{dict(sent)}。\n- [Insight] Top positive: {top_pos}.\n- [Insight] Top negative: {top_neg}.\n- [Data Gap] 缺少上期同口径完整 Amazon 样本，趋势与下降结论均为 Not Available。\n",encoding="utf-8")
    (out/"full_review_analysis.md").write_text(f"# Full Review Analysis — SwitchBot AI Art Canvas / Amazon Japan\n\n## Conclusion\n\n- [Fact] 分析 {len(rows)} 条可审计 Amazon Japan 评论，平均评分 {data['kpis']['average_rating']}；覆盖 73/90，Partial。\n- [Insight] 正向价值集中于 {top_pos}。\n- [Insight] 主要问题集中于 {top_neg}。\n- [Data Gap] Amazon 仍有 17 条正文未能从公开分页取得，不进行全量市场占比推断。\n\n## Priority issues\n\n"+"\n".join(f"- {x['priority']} {x['issue']}: {x['occurrences']} 条，score {x['priority_score']}，confidence {x['confidence']}" for x in issue_rows)+"\n",encoding="utf-8")
    html="""<!doctype html><meta charset='utf-8'><title>VOC Dashboard</title><style>body{font:14px system-ui;margin:0;background:#f5f7fb;color:#172033}header{padding:24px 5%;background:#111827;color:white}.wrap{padding:20px 5%}.filters,.cards{display:flex;gap:12px;flex-wrap:wrap}.card,.panel{background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px #0001}.card{min-width:150px}.card b{font-size:26px;display:block}.panel{margin-top:16px}select{padding:8px}table{width:100%;border-collapse:collapse}th,td{padding:8px;border-bottom:1px solid #e5e7eb;text-align:left}th{position:sticky;top:0;background:#f8fafc}.bar{height:10px;background:#2563eb;border-radius:5px}.warn{color:#b45309}.scroll{max-height:460px;overflow:auto}</style><header><h1>Customer Review Intelligence</h1><div>SwitchBot AI Art Canvas · Amazon Japan · 2025–2026</div></header><main class='wrap'><p class='warn'><b>Partial:</b> 73 / 90 displayed text reviews auditable. Missing reviews are not zero.</p><div class='filters'><select id='sent'><option value=''>All sentiments</option></select><select id='rating'><option value=''>All ratings</option></select><select id='topic'><option value=''>All topics</option></select></div><div class='cards' id='cards'></div><section class='panel'><h2>Issue priority</h2><div id='issues'></div></section><section class='panel'><h2>User voices</h2><div class='scroll'><table><thead><tr><th>Date</th><th>Rating</th><th>Sentiment</th><th>Topic</th><th>Original Japanese</th><th>Source</th></tr></thead><tbody id='voices'></tbody></table></div></section></main><script>const DATA="""+json.dumps(data,ensure_ascii=False)+""";const voices=DATA.voices;function opts(id,key){[...new Set(voices.map(x=>x[key]).filter(Boolean))].sort().forEach(v=>document.getElementById(id).insertAdjacentHTML('beforeend',`<option>${v}</option>`))}opts('sent','sentiment');opts('rating','rating');opts('topic','primary_topic');function render(){let r=voices.filter(x=>(!sent.value||x.sentiment==sent.value)&&(!rating.value||x.rating==rating.value)&&(!topic.value||x.primary_topic==topic.value));let avg=r.length?r.reduce((a,x)=>a+(+x.rating||0),0)/r.length:0;let neg=r.filter(x=>['Negative','Strong Negative'].includes(x.sentiment)).length;cards.innerHTML=`<div class=card>Reviews<b>${r.length}</b></div><div class=card>Avg rating<b>${avg.toFixed(2)}</b></div><div class=card>Negative rate<b>${r.length?(neg/r.length*100).toFixed(1):0}%</b></div><div class=card>P0/P1 issues<b>${DATA.kpis.p0_p1}</b></div>`;issues.innerHTML=DATA.issues.slice(0,10).map(x=>`<p><b>${x.priority} ${x.issue}</b> · ${x.occurrences} reviews · score ${x.priority_score}<div class=bar style='width:${x.priority_score}%'></div></p>`).join('');document.getElementById('voices').innerHTML=r.map(x=>`<tr><td>${x.review_date||''}</td><td>${x.rating||''}</td><td>${x.sentiment}</td><td>${x.primary_topic||''}</td><td>${(x.original_japanese||'').replaceAll('<','&lt;')}</td><td><a href='${x.source_url}' target=_blank>Amazon</a></td></tr>`).join('')}document.querySelectorAll('select').forEach(x=>x.onchange=render);render()</script>"""
    (out/"review_dashboard.html").write_text(html,encoding="utf-8")
    print(json.dumps({"records":len(rows),"issues":len(issue_rows),"outputs":str(out)},ensure_ascii=False))
if __name__=="__main__": main()
