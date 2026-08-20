#!/usr/bin/env python3
"""Auditable official-API collectors for YouTube comments and X posts.

Credentials are read only from environment variables. Every response page is
saved before normalization, and a resume token is persisted after each page.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def request_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def save_page(raw_dir: Path, stem: str, payload: dict) -> dict:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{stem}.json"
    body = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    path.write_bytes(body)
    return {"path": str(path), "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "immutable": True}


def is_natural_comment(text: str) -> tuple[str, str]:
    lowered = text.casefold()
    if any(term in lowered for term in ("#pr", "広告", "アフィリエイト", "amazon.co.jp/dp/", "prtimes")):
        return "Context Only", "promotion_or_syndication_marker"
    opinion = any(term in text for term in (
        "欲しい", "買った", "購入", "使って", "便利", "良い", "いい", "悪い", "暗い", "高い",
        "残念", "気になる", "好き", "素敵", "アプリ", "設置", "画質", "発色", "サイズ", "飾",
    ))
    return ("Natural VOC", "explicit_user_opinion") if opinion else ("Unverified", "product_opinion_not_explicit")


def youtube(args: argparse.Namespace) -> dict:
    key = os.environ.get(args.api_key_env, "")
    if not key:
        raise SystemExit(f"Missing environment variable: {args.api_key_env}")
    videos = json.loads(Path(args.videos_json).read_text(encoding="utf-8"))
    video_ids = [item.get("videoId") if isinstance(item, dict) else str(item) for item in videos]
    raw_dir, state_path = Path(args.raw_dir), Path(args.resume_state)
    state = json.loads(state_path.read_text()) if state_path.exists() else {"videos": {}}
    records, files, failures = [], [], []
    for video_id in filter(None, video_ids):
        token = (state["videos"].get(video_id) or {}).get("next_page_token", "")
        page_no = (state["videos"].get(video_id) or {}).get("pages", 0) + 1
        while True:
            params = {"part": "snippet,replies", "videoId": video_id, "maxResults": 100, "order": "time", "textFormat": "plainText", "key": key}
            if token: params["pageToken"] = token
            url = "https://www.googleapis.com/youtube/v3/commentThreads?" + urllib.parse.urlencode(params)
            try:
                payload = request_json(url)
            except urllib.error.HTTPError as exc:
                failures.append({"video_id": video_id, "page": page_no, "status": exc.code, "reason": exc.read().decode("utf-8", "replace")[:1000]})
                break
            files.append(save_page(raw_dir / video_id, f"threads-page-{page_no:04d}", payload))
            for thread in payload.get("items", []):
                top = ((thread.get("snippet") or {}).get("topLevelComment") or {})
                comments = [top, *((thread.get("replies") or {}).get("comments") or [])]
                total_replies = int((thread.get("snippet") or {}).get("totalReplyCount") or 0)
                embedded_replies = max(0, len(comments) - 1)
                if total_replies > embedded_replies and top.get("id"):
                    reply_token, reply_page = "", 1
                    comments = [top]
                    while True:
                        rp = {"part": "snippet", "parentId": top["id"], "maxResults": 100, "textFormat": "plainText", "key": key}
                        if reply_token: rp["pageToken"] = reply_token
                        reply_payload = request_json("https://www.googleapis.com/youtube/v3/comments?" + urllib.parse.urlencode(rp))
                        files.append(save_page(raw_dir / video_id, f"replies-{top['id']}-page-{reply_page:04d}", reply_payload))
                        comments.extend(reply_payload.get("items", []))
                        reply_token = reply_payload.get("nextPageToken", "")
                        if not reply_token: break
                        reply_page += 1
                for comment in comments:
                    snippet = comment.get("snippet") or {}
                    text = snippet.get("textDisplay") or snippet.get("textOriginal") or ""
                    published = str(snippet.get("publishedAt") or "")[:10]
                    if published and not args.date_from <= published <= args.date_to: continue
                    eligibility, basis = is_natural_comment(text)
                    records.append({
                        "source": "youtube", "source_review_id": comment.get("id", ""), "product_id": args.product_id,
                        "record_type": "comment", "relationship_type": "organic", "voc_eligibility": eligibility,
                        "channel_product_name": args.product_name, "channel_product_url": f"https://www.youtube.com/watch?v={video_id}",
                        "review_url": f"https://www.youtube.com/watch?v={video_id}&lc={comment.get('id','')}",
                        "review_body": text, "review_date": published, "reviewer_display_name": snippet.get("authorDisplayName", ""),
                        "helpful_votes": snippet.get("likeCount", ""), "verified_purchase": "Unknown",
                        "notes": f"official_youtube_api; eligibility_basis={basis}", "coverage_status": "Complete",
                    })
            token = payload.get("nextPageToken", "")
            state["videos"][video_id] = {"pages": page_no, "next_page_token": token, "complete": not bool(token)}
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
            if not token: break
            page_no += 1
    return {"source": "youtube", "records": records, "files": files, "failures": failures, "coverage_status": "Complete" if not failures and all(v.get("complete") for v in state["videos"].values()) else "Partial", "state": state}


def x_full_archive(args: argparse.Namespace) -> dict:
    token = os.environ.get(args.bearer_env, "")
    if not token: raise SystemExit(f"Missing environment variable: {args.bearer_env}")
    raw_dir, state_path = Path(args.raw_dir), Path(args.resume_state)
    state = json.loads(state_path.read_text()) if state_path.exists() else {"next_token": "", "pages": 0, "complete": False}
    next_token, page_no, records, files, failures = state.get("next_token", ""), state.get("pages", 0) + 1, [], [], []
    while True:
        params = {
            "query": args.query, "start_time": f"{args.date_from}T00:00:00Z", "end_time": f"{args.date_to}T23:59:59Z",
            "max_results": 500, "tweet.fields": "created_at,public_metrics,author_id,lang,conversation_id",
            "expansions": "author_id", "user.fields": "username,name",
        }
        if next_token: params["next_token"] = next_token
        url = "https://api.x.com/2/tweets/search/all?" + urllib.parse.urlencode(params)
        try: payload = request_json(url, {"Authorization": f"Bearer {token}", "Accept": "application/json"})
        except urllib.error.HTTPError as exc:
            failures.append({"page": page_no, "status": exc.code, "reason": exc.read().decode("utf-8", "replace")[:1000]}); break
        files.append(save_page(raw_dir, f"posts-page-{page_no:04d}", payload))
        users = {u.get("id"): u for u in (payload.get("includes") or {}).get("users", [])}
        for post in payload.get("data", []):
            text = post.get("text", ""); eligibility, basis = is_natural_comment(text); author = users.get(post.get("author_id"), {})
            metrics = post.get("public_metrics") or {}
            records.append({
                "source": "x", "source_review_id": post.get("id", ""), "product_id": args.product_id,
                "record_type": "sns_post", "relationship_type": "organic" if eligibility != "Context Only" else "syndicated",
                "voc_eligibility": eligibility, "channel_product_name": args.product_name,
                "channel_product_url": args.product_url, "review_url": f"https://x.com/{author.get('username','i')}/status/{post.get('id','')}",
                "review_body": text, "review_date": str(post.get("created_at") or "")[:10],
                "reviewer_display_name": author.get("name", ""), "helpful_votes": metrics.get("like_count", ""),
                "verified_purchase": "Unknown", "notes": f"official_x_api_full_archive; eligibility_basis={basis}; metrics={json.dumps(metrics, sort_keys=True)}",
                "coverage_status": "Complete",
            })
        next_token = (payload.get("meta") or {}).get("next_token", "")
        state = {"next_token": next_token, "pages": page_no, "complete": not bool(next_token), "query": args.query, "date_from": args.date_from, "date_to": args.date_to}
        state_path.parent.mkdir(parents=True, exist_ok=True); state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        if not next_token: break
        page_no += 1
    return {"source": "x", "records": records, "files": files, "failures": failures, "coverage_status": "Complete" if state.get("complete") and not failures else "Partial", "state": state}


def main() -> int:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="channel", required=True)
    common = argparse.ArgumentParser(add_help=False)
    for flag, default in (("--product-id", "ai_art_canvas"), ("--product-name", "SwitchBot AIアートキャンバス"), ("--date-from", "2025-01-01"), ("--date-to", "2026-07-31")):
        common.add_argument(flag, default=default)
    common.add_argument("--raw-dir", required=True); common.add_argument("--resume-state", required=True); common.add_argument("--output", required=True)
    yp = sub.add_parser("youtube", parents=[common]); yp.add_argument("--videos-json", required=True); yp.add_argument("--api-key-env", default="YOUTUBE_API_KEY")
    xp = sub.add_parser("x", parents=[common]); xp.add_argument("--query", required=True); xp.add_argument("--bearer-env", default="X_BEARER_TOKEN"); xp.add_argument("--product-url", default="https://www.switchbot.jp/products/switchbot-ai-art-frame")
    args = p.parse_args(); result = youtube(args) if args.channel == "youtube" else x_full_archive(args)
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source": result["source"], "records": len(result["records"]), "status": result["coverage_status"], "failures": len(result["failures"])}, ensure_ascii=False)); return 0


if __name__ == "__main__": raise SystemExit(main())
