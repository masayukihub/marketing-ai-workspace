from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from review_core import map_products, normalize_record


def index() -> dict:
    return {
        "validation_status": "pass",
        "products": [{"product_id": "lock_ultra"}, {"product_id": "hub_3"}],
        "entities": [
            {
                "entity_id": "variant:lock-ultra:black",
                "product_id": "lock_ultra",
                "variant_id": "lock_ultra_black",
                "bundle_id": "",
            },
            {
                "entity_id": "bundle:lock-ultra:vision",
                "product_id": "lock_ultra",
                "variant_id": "",
                "bundle_id": "lock_ultra_vision_bundle",
            },
        ],
        "identifier_lookup": {
            "asin": {
                "ASIN-BLACK": ["variant:lock-ultra:black"],
                "ASIN-BUNDLE": ["bundle:lock-ultra:vision"],
            },
            "sku": {},
            "jan": {},
            "model_number": {},
        },
        "alias_lookup": {"Lock Ultra": ["lock_ultra"], "Hub 3": ["hub_3"]},
    }


def row(**overrides) -> dict:
    raw = {
        "source": "amazon_jp",
        "review_url": "https://example.com/review",
        "review_body": "便利",
        "channel_product_name": "",
    }
    raw.update(overrides)
    return normalize_record(raw, batch_id="test")


def test_identifier_maps_variant_and_bundle() -> None:
    variant, bundle = map_products(
        [row(asin="ASIN-BLACK"), row(asin="ASIN-BUNDLE")],
        index(),
    )
    assert variant["mapping_status"] == "Confirmed"
    assert variant["variant_id"] == "lock_ultra_black"
    assert bundle["mapping_status"] == "Confirmed"
    assert bundle["bundle_id"] == "lock_ultra_vision_bundle"


def test_exact_alias_maps_and_unknown_fails_closed() -> None:
    exact, unknown = map_products(
        [row(channel_product_name="Hub 3"), row(channel_product_name="Ultra")],
        index(),
    )
    assert exact["product_id"] == "hub_3"
    assert exact["mapping_status"] == "Confirmed"
    assert unknown["mapping_status"] == "Unmapped"
    assert unknown["manual_review_required"] == "Yes"


def test_conflicting_identifiers_fail_closed() -> None:
    payload = index()
    payload["identifier_lookup"]["asin"]["BAD"] = [
        "variant:lock-ultra:black",
        "bundle:lock-ultra:vision",
    ]
    mapped = map_products([row(asin="BAD")], payload)[0]
    assert mapped["mapping_status"] == "Conflicting"
    assert mapped["manual_review_required"] == "Yes"


def test_unresolved_bundle_does_not_map_to_product_as_confirmed() -> None:
    mapped = map_products(
        [row(product_id="lock_ultra", variant_text="Lock Ultra 色:ブラック | 顔認証パッドのモデル:顔認証パッドPro")],
        index(),
    )[0]
    assert mapped["mapping_status"] == "Probable"
    assert mapped["bundle_id"] == ""
    assert mapped["manual_review_required"] == "Yes"
