from __future__ import annotations

import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from review_core import classify_rows, load_yaml, normalize_record

WORKSPACE = SKILL
SENTIMENT = load_yaml(WORKSPACE / "config" / "sentiment_rules.yaml")
TAXONOMY = load_yaml(WORKSPACE / "config" / "taxonomy.yaml")


def classified(text: str, rating: int = 3) -> dict:
    row = normalize_record(
        {
            "source": "amazon_jp",
            "product_id": "lock_ultra",
            "review_url": "https://example.com/review",
            "review_body": text,
            "rating": rating,
            "mapping_status": "Confirmed",
        },
        batch_id="test",
    )
    return classify_rows([row], SENTIMENT, TAXONOMY)[0]


def test_recovery_is_not_pure_negative() -> None:
    row = classified("接続できないと思ったが、設定をやり直したら問題なく使えた", 5)
    assert row["sentiment"] == "Mixed"
    assert row["manual_review_required"] == "Yes"


def test_rating_and_text_are_separate() -> None:
    row = classified("便利だがアプリが使いにくい", 5)
    assert row["sentiment"] == "Mixed"
    assert row["primary_topic"] in {"App", "Positive Experience"}


def test_critical_and_return_risk_are_escalated() -> None:
    row = classified("本体が過熱して煙が出た。返金してほしい", 1)
    assert row["severity"] == "Critical"
    assert row["return_intent"] == "Yes"
    assert row["manual_review_required"] == "Yes"


def test_art_canvas_display_and_capacity_are_auditable() -> None:
    row = classified("画面が暗すぎるうえ、ローカルには10枚までしか保存できないのが残念", 2)
    assert row["sentiment"] == "Negative"
    assert row["primary_topic"] == "Display Quality"
    assert "Content Capacity" in row["secondary_topics"]
    assert row["hardware_related"] == "Yes"
    assert row["app_related"] == "Yes"
    assert "10枚" in row["expectation_gap"]
