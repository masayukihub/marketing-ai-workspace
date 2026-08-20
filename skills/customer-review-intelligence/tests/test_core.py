from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from review_core import assign_duplicates, extract_jsonld_reviews, extract_rakuten_state_reviews, merge_incremental, normalize_record


def base_record(body: str = "便利で使いやすい") -> dict:
    return {
        "source": "amazon_jp",
        "source_review_id": "R-001",
        "product_id": "lock_ultra",
        "channel_product_url": "https://example.com/product",
        "review_url": "https://example.com/review/R-001",
        "rating": 5,
        "review_body": body,
        "review_date": "2026-07-01",
        "reviewer_display_name": "public-name",
    }


def test_stable_id_and_version_change() -> None:
    first = normalize_record(base_record(), batch_id="a")
    second = normalize_record(base_record(), batch_id="b")
    updated = normalize_record(base_record("便利だが接続できない"), batch_id="c")
    assert first["review_id"] == second["review_id"] == updated["review_id"]
    assert first["version_id"] == second["version_id"]
    assert first["version_id"] != updated["version_id"]


def test_incremental_is_idempotent_and_preserves_update(tmp_path: Path) -> None:
    first = normalize_record(base_record(), batch_id="a")
    canonical, versions, counts = merge_incremental(tmp_path, [first])
    assert counts == {"new": 1, "updated": 0, "unchanged": 0}
    assert len(canonical) == len(versions) == 1
    _, versions, counts = merge_incremental(tmp_path, [dict(first)])
    assert counts == {"new": 0, "updated": 0, "unchanged": 1}
    assert len(versions) == 1
    changed = normalize_record(base_record("返品したい。全く使えない"), batch_id="b")
    canonical, versions, counts = merge_incremental(tmp_path, [changed])
    assert counts["updated"] == 1
    assert canonical[0]["review_status"] == "Updated"
    assert len(versions) == 2


def test_star_only_incomplete_review_is_idempotent(tmp_path: Path) -> None:
    raw = base_record("")
    raw["review_title"] = ""
    first = normalize_record(raw, batch_id="a")
    assert first["review_status"] == "Incomplete"
    merge_incremental(tmp_path, [first])
    _, _, counts = merge_incremental(tmp_path, [normalize_record(raw, batch_id="b")])
    assert counts == {"new": 0, "updated": 0, "unchanged": 1}


def test_timestamp_date_is_normalized() -> None:
    raw = base_record()
    raw["review_date"] = "2026-06-29 05:00:06 UTC"
    assert normalize_record(raw, batch_id="a")["review_date"] == "2026-06-29"


def test_cross_channel_duplicate_is_grouped_not_deleted() -> None:
    first = normalize_record(base_record(), batch_id="a")
    second_raw = base_record()
    second_raw["source"] = "rakuten"
    second_raw["source_review_id"] = "RK-9"
    second = normalize_record(second_raw, batch_id="a")
    rows = assign_duplicates([first, second])
    assert len(rows) == 2
    assert {row["duplicate_type"] for row in rows} == {"Cross-Channel Duplicate"}
    assert len({row["duplicate_group_id"] for row in rows}) == 1


def test_rakuten_embedded_state_extracts_auditable_text() -> None:
    state = {
        "apiData": {
            "reviewInfo": {
                "reviews": [{
                    "encryptedEasyId": "abc",
                    "item_id": 10,
                    "reg_time": "2026-07-31T10:00:00+09:00",
                    "evaluation": 4,
                    "review": "便利だが設定は少し難しい",
                    "nickname": "reviewer",
                    "review_theme": "使用感",
                    "item_url": "https://example.com/item",
                    "item_sku_info": "Black",
                }]
            }
        }
    }
    page = f"<script type='application/ld+json'>{{\"@type\":\"Review\",\"reviewRating\":{{\"ratingValue\":4}}}}</script><script>window.__INITIAL_STATE__ = {__import__('json').dumps(state, ensure_ascii=False)};</script>"
    assert extract_jsonld_reviews(page, "https://example.com", "rakuten", "hub_3") == []
    rows = extract_rakuten_state_reviews(page, "https://example.com", "rakuten", "hub_3")
    assert len(rows) == 1
    assert rows[0]["review_body"] == "便利だが設定は少し難しい"
    assert rows[0]["review_date"] == "2026-07-31"
    assert rows[0]["source_review_id"].startswith("abc|10|")
