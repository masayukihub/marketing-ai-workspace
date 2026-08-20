#!/usr/bin/env python3
"""Deterministic core for Customer Review Intelligence."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ModuleNotFoundError:  # macOS system Python fallback; Ruby YAML is part of the OS toolchain.
    yaml = None

SENTIMENTS = {"Positive", "Neutral", "Negative", "Mixed"}
SEVERITIES = {"Low", "Medium", "High", "Critical"}
MAPPING_STATUSES = {"Confirmed", "Probable", "Unmapped", "Conflicting"}
COVERAGE_STATUSES = {"Complete", "Zero Confirmed", "Partial", "Blocked", "Not Configured"}
REVIEW_STATUSES = {"Active", "Updated", "Deleted", "Incomplete"}
YES_NO_UNKNOWN = {"Yes", "No", "Unknown"}

REVIEW_COLUMNS = [
    "review_id", "version_id", "batch_id", "source", "source_review_id",
    "source_id", "record_type", "relationship_type", "voc_eligibility",
    "product_id", "variant_id", "bundle_id", "asin", "sku", "jan",
    "model_number", "mapping_status", "mapping_basis",
    "channel_product_name", "channel_product_url", "source_url", "review_url", "rating",
    "review_title", "review_body", "review_date", "collected_at",
    "reviewer_display_name", "verified_purchase", "helpful_votes", "variant_text",
    "language", "review_status", "coverage_status", "original_review_hash",
    "duplicate_type", "duplicate_group_id", "canonical_review_id", "raw_file_path",
    "last_checked_at", "sentiment", "sentiment_score", "primary_topic",
    "secondary_topics", "issue_category", "issue_subcategory",
    "purchase_motivation", "usage_scenario", "praised_feature",
    "complained_feature", "expectation_gap", "severity", "return_intent",
    "support_contacted", "firmware_related", "installation_related",
    "app_related", "hardware_related", "logistics_related",
    "analysis_confidence", "classification_basis", "manual_review_required",
    "responsibility_owner", "notes",
]
REPORT_COLUMNS = [column for column in REVIEW_COLUMNS if column != "reviewer_display_name"]

FIELD_ALIASES = {
    "platform": "source",
    "content": "review_body",
    "body": "review_body",
    "title": "review_title",
    "date": "review_date",
    "url": "review_url",
    "source_url": "review_url",
    "author": "reviewer_display_name",
    "reviewer": "reviewer_display_name",
    "engagement": "helpful_votes",
    "product": "channel_product_name",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def batch_id_now() -> str:
    return datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    if yaml is not None:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        completed = subprocess.run(
            ["ruby", "-ryaml", "-rjson", "-e", "puts YAML.safe_load(File.read(ARGV[0]), aliases: true).to_json", str(path)],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(completed.stdout)
    return payload or {}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", html.unescape(str(value))).strip()


def normalize_key(value: str) -> str:
    return re.sub(r"[\s\u3000・_\-]+", "", clean_text(value)).casefold()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_review_id(record: dict[str, Any]) -> str:
    source = clean_text(record.get("source"))
    source_review_id = clean_text(record.get("source_review_id"))
    if source_review_id:
        identity = f"{source}|{source_review_id}"
    else:
        identity = "|".join(clean_text(record.get(key)) for key in (
            "source", "product_id", "channel_product_url", "rating", "review_date",
            "review_title", "review_body", "reviewer_display_name",
        ))
    return f"rev_{sha256_text(identity)[:24]}"


def content_hash(record: dict[str, Any]) -> str:
    content = "|".join(clean_text(record.get(key)) for key in (
        "rating", "review_title", "review_body", "review_date", "variant_text",
    ))
    return sha256_text(content)


def normalize_bool(value: Any) -> str:
    token = clean_text(value).casefold()
    if token in {"yes", "true", "1", "はい", "verified", "購入済み"}:
        return "Yes"
    if token in {"no", "false", "0", "いいえ"}:
        return "No"
    return "Unknown"


def normalize_rating(value: Any) -> str:
    match = re.search(r"\d+(?:\.\d+)?", clean_text(value))
    if not match:
        return ""
    rating = float(match.group())
    if rating < 0 or rating > 5:
        return ""
    return str(int(rating)) if rating.is_integer() else str(rating)


def infer_language(text: str) -> str:
    if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text):
        return "ja"
    return "und"


def normalize_date(value: Any) -> str:
    text = clean_text(value)
    match = re.search(r"(20\d{2})[-年/](\d{1,2})[-月/](\d{1,2})", text)
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}" if match else text


def infer_record_type(source: str, supplied: str = "") -> str:
    if supplied:
        return supplied
    key = normalize_key(source)
    if key in {"amazonjp", "amazon", "rakuten", "楽天市場", "yahooshopping", "switchbotofficial"}:
        return "ec_review"
    if key == "youtube":
        return "comment"
    if key == "x":
        return "sns_post"
    return "imported_record"


def infer_relationship(record_type: str, supplied: str = "") -> str:
    if supplied:
        return supplied
    return "organic" if record_type in {"ec_review", "sns_post", "comment"} else "unknown"


def infer_voc_eligibility(record_type: str, relationship: str) -> str:
    if relationship in {"paid_kol", "pr_placement", "syndicated", "owned"}:
        return "Context Only" if record_type in {"kol_content", "media_article", "official_post"} else "Unverified"
    if record_type in {"ec_review", "sns_post", "comment"} and relationship == "organic":
        return "Natural VOC"
    return "Unverified"


def normalize_record(
    raw: dict[str, Any],
    *,
    batch_id: str,
    raw_file_path: str = "",
    default_source: str = "",
    default_product_id: str = "",
    coverage_status: str = "Complete",
) -> dict[str, str]:
    remapped: dict[str, Any] = {}
    for key, value in raw.items():
        remapped[FIELD_ALIASES.get(key, key)] = value
    source = clean_text(remapped.get("source") or default_source)
    record_type = infer_record_type(source, clean_text(remapped.get("record_type")))
    relationship = infer_relationship(record_type, clean_text(remapped.get("relationship_type")))
    text = clean_text(remapped.get("review_body"))
    timestamp = clean_text(remapped.get("collected_at")) or now_iso()
    row = {column: "" for column in REVIEW_COLUMNS}
    row.update({
        "batch_id": batch_id,
        "source": source,
        "source_review_id": clean_text(remapped.get("source_review_id")),
        "source_id": clean_text(remapped.get("source_id")) or normalize_key(source),
        "record_type": record_type,
        "relationship_type": relationship,
        "voc_eligibility": clean_text(remapped.get("voc_eligibility")) or infer_voc_eligibility(record_type, relationship),
        "product_id": clean_text(remapped.get("product_id")) or default_product_id,
        "variant_id": clean_text(remapped.get("variant_id")),
        "bundle_id": clean_text(remapped.get("bundle_id")),
        "asin": clean_text(remapped.get("asin")),
        "sku": clean_text(remapped.get("sku")),
        "jan": clean_text(remapped.get("jan")),
        "model_number": clean_text(remapped.get("model_number")),
        "mapping_status": clean_text(remapped.get("mapping_status")),
        "mapping_basis": clean_text(remapped.get("mapping_basis")),
        "channel_product_name": clean_text(remapped.get("channel_product_name")),
        "channel_product_url": clean_text(remapped.get("channel_product_url")),
        "source_url": clean_text(remapped.get("source_url") or remapped.get("review_url") or remapped.get("channel_product_url")),
        "review_url": clean_text(remapped.get("review_url") or remapped.get("channel_product_url")),
        "rating": normalize_rating(remapped.get("rating")),
        "review_title": clean_text(remapped.get("review_title")),
        "review_body": text,
        "review_date": normalize_date(remapped.get("review_date")),
        "collected_at": timestamp,
        "reviewer_display_name": clean_text(remapped.get("reviewer_display_name")),
        "verified_purchase": normalize_bool(remapped.get("verified_purchase")),
        "helpful_votes": clean_text(remapped.get("helpful_votes")),
        "variant_text": clean_text(remapped.get("variant_text")),
        "language": clean_text(remapped.get("language")) or infer_language(text),
        "review_status": clean_text(remapped.get("review_status")) or ("Incomplete" if not text else "Active"),
        "coverage_status": coverage_status,
        "raw_file_path": raw_file_path,
        "last_checked_at": timestamp,
        "return_intent": normalize_bool(remapped.get("return_intent")),
        "support_contacted": normalize_bool(remapped.get("support_contacted")),
        "firmware_related": normalize_bool(remapped.get("firmware_related")),
        "notes": clean_text(remapped.get("notes")),
    })
    row["original_review_hash"] = content_hash(row)
    row["review_id"] = clean_text(remapped.get("review_id")) or stable_review_id(row)
    row["version_id"] = f"{row['review_id']}_{row['original_review_hash'][:12]}"
    return row


class JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.capture = False
        self.buffer: list[str] = []
        self.payloads: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "script":
            return
        attr_map = {key.casefold(): (value or "") for key, value in attrs}
        self.capture = "ld+json" in attr_map.get("type", "").casefold()
        self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "script" and self.capture:
            self.payloads.append("".join(self.buffer))
            self.capture = False
            self.buffer = []


def _walk_json(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_json(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_json(nested)


def extract_jsonld_reviews(page_text: str, page_url: str, source: str, product_id: str) -> list[dict[str, Any]]:
    parser = JsonLdParser()
    parser.feed(page_text)
    records: list[dict[str, Any]] = []
    for payload in parser.payloads:
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue
        for item in _walk_json(parsed):
            item_type = item.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]
            if "Review" not in types and not {"reviewBody", "reviewRating"} & set(item):
                continue
            rating_value = item.get("reviewRating", {})
            if isinstance(rating_value, dict):
                rating_value = rating_value.get("ratingValue", "")
            author = item.get("author", "")
            if isinstance(author, dict):
                author = author.get("name", "")
            review_title = item.get("name") or item.get("headline") or ""
            review_body = item.get("reviewBody") or item.get("description") or ""
            # Aggregate pages sometimes expose only author/rating shells in JSON-LD.
            # They are evidence of a listing, but not analyzable VOC records.
            if not clean_text(review_title) and not clean_text(review_body):
                continue
            records.append({
                "source": source,
                "source_review_id": item.get("@id") or item.get("url") or "",
                "product_id": product_id,
                "channel_product_url": page_url,
                "review_url": item.get("url") or page_url,
                "rating": rating_value,
                "review_title": review_title,
                "review_body": review_body,
                "review_date": item.get("datePublished") or "",
                "reviewer_display_name": author,
                "verified_purchase": "Unknown",
            })
    return records


def extract_rakuten_state_reviews(
    page_text: str, page_url: str, source: str, product_id: str
) -> list[dict[str, Any]]:
    """Extract Rakuten's public first-page review state without calling private APIs."""
    marker = "window.__INITIAL_STATE__ = "
    start = page_text.find(marker)
    if start < 0:
        return []
    decoder = json.JSONDecoder()
    try:
        state, _ = decoder.raw_decode(page_text[start + len(marker):])
    except json.JSONDecodeError:
        return []
    reviews = (((state.get("apiData") or {}).get("reviewInfo") or {}).get("reviews") or [])
    records: list[dict[str, Any]] = []
    for item in reviews:
        body = clean_text(item.get("review"))
        if not body:
            continue
        published = clean_text(item.get("reg_time"))
        review_date = published[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", published) else published
        source_review_id = "|".join(
            clean_text(item.get(key)) for key in ("encryptedEasyId", "item_id", "reg_time")
        )
        records.append({
            "source": source,
            "source_review_id": source_review_id,
            "product_id": product_id,
            "channel_product_url": page_url,
            "review_url": item.get("item_url") or page_url,
            "rating": item.get("evaluation"),
            "review_title": item.get("review_theme") or "",
            "review_body": body,
            "review_date": review_date,
            "reviewer_display_name": item.get("nickname") or "",
            "verified_purchase": "Unknown",
            "variant_text": item.get("item_sku_info") or "",
        })
    return records


def fetch_public_page(url: str, timeout: int = 30) -> tuple[str, int, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SwitchBot-VOC-Audit/1.0; public-page-only)",
            "Accept-Language": "ja,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            return body, int(response.status), ""
    except urllib.error.HTTPError as exc:
        return "", int(exc.code), f"HTTP {exc.code}"
    except Exception as exc:  # network and TLS are reported, never hidden
        return "", 0, f"{type(exc).__name__}: {exc}"


def collect_public_pages(
    workspace: Path,
    products_config: dict[str, Any],
    sources_config: dict[str, Any],
    selected_products: set[str],
    selected_modules: set[str],
    batch_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_specs = sources_config.get("sources", {})
    records: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for product in products_config.get("products", []):
        product_id = clean_text(product.get("product_id"))
        if selected_products and product_id not in selected_products:
            continue
        for source, link_spec in (product.get("sources") or {}).items():
            source_spec = source_specs.get(source, {})
            module = clean_text(source_spec.get("module")) or "ec"
            if selected_modules and module not in selected_modules:
                continue
            url = clean_text((link_spec or {}).get("url"))
            required = bool((link_spec or {}).get("required"))
            entry = {
                "product_id": product_id,
                "source": source,
                "module": module,
                "url": url,
                "required": required,
                "coverage_status": "Not Configured",
                "records": 0,
                "http_status": "",
                "failure_reason": "",
                "pagination_boundary": "not checked",
            }
            if not url:
                entry["failure_reason"] = "Product review URL is not configured."
                coverage.append(entry)
                continue
            page_text, status, failure = fetch_public_page(url)
            entry["http_status"] = status
            if failure:
                fallback_paths = sorted(
                    path for path in (workspace / "raw" / source).glob(f"*/{product_id}.html")
                    if path.parent.name != batch_id
                )
                if fallback_paths:
                    fallback_path = fallback_paths[-1]
                    page_text = fallback_path.read_text(encoding="utf-8")
                    entry["coverage_status"] = "Partial"
                    entry["failure_reason"] = f"{failure}; replayed prior immutable snapshot."
                    entry["pagination_boundary"] = f"Fallback snapshot: {fallback_path.relative_to(workspace)}"
                    files.append({
                        "path": str(fallback_path.relative_to(workspace)),
                        "sha256": sha256_file(fallback_path),
                        "bytes": fallback_path.stat().st_size,
                        "replayed": True,
                    })
                else:
                    entry["coverage_status"] = "Blocked"
                    entry["failure_reason"] = failure
                    coverage.append(entry)
                    continue
            if "replayed prior immutable snapshot" in entry["failure_reason"]:
                raw_path = fallback_path
            else:
                target_dir = workspace / "raw" / source / batch_id
                target_dir.mkdir(parents=True, exist_ok=True)
                raw_path = target_dir / f"{product_id}.html"
                if raw_path.exists():
                    existing_hash = sha256_file(raw_path)
                    fetched_hash = sha256_text(page_text)
                    if existing_hash != fetched_hash:
                        entry["coverage_status"] = "Blocked"
                        entry["failure_reason"] = "Immutable snapshot collision: batch path already contains different bytes."
                        coverage.append(entry)
                        continue
                else:
                    raw_path.write_text(page_text, encoding="utf-8")
                files.append({
                    "path": str(raw_path.relative_to(workspace)),
                    "sha256": sha256_file(raw_path),
                    "bytes": raw_path.stat().st_size,
                })
            lower = page_text.casefold()
            if any(token in lower for token in ("captcha", "robot check", "ログインしてください", "access denied")):
                entry["coverage_status"] = "Blocked"
                entry["failure_reason"] = "Page requires login, CAPTCHA, or access verification."
                coverage.append(entry)
                continue
            extracted = extract_jsonld_reviews(page_text, url, source, product_id)
            if source == "rakuten":
                embedded = extract_rakuten_state_reviews(page_text, url, source, product_id)
                seen = {clean_text(row.get("source_review_id")) for row in extracted}
                extracted.extend(
                    row for row in embedded
                    if clean_text(row.get("source_review_id")) not in seen
                )
            raw_relative = str(raw_path.relative_to(workspace))
            for record in extracted:
                record["_raw_file_path"] = raw_relative
                record["coverage_status"] = "Partial"
            records.extend(extracted)
            entry["records"] = len(extracted)
            entry["coverage_status"] = "Partial"
            if "replayed prior immutable snapshot" not in entry["failure_reason"]:
                entry["pagination_boundary"] = "JSON-LD on first fetched page only; browser pagination not verified"
            if not extracted:
                entry["failure_reason"] = "Public page loaded but no auditable review objects were extractable."
            coverage.append(entry)
    manifest = {
        "schema_version": "1.0",
        "batch_id": batch_id,
        "collected_at": now_iso(),
        "coverage": coverage,
        "files": files,
    }
    manifest_path = workspace / "raw" / f"manifest-{batch_id}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records, manifest


def load_input_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix in {".json", ".jsonl"}:
        text = path.read_text(encoding="utf-8-sig")
        if suffix == ".jsonl":
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        value = json.loads(text)
        return value if isinstance(value, list) else value.get("records", [])
    raise ValueError(f"Unsupported input: {path}")


def load_product_index(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("validation_status") != "pass":
        raise ValueError("Product Knowledge index validation_status is not pass")
    return payload


def map_products(rows: list[dict[str, str]], product_index: dict[str, Any]) -> list[dict[str, str]]:
    products = {item.get("product_id"): item for item in product_index.get("products", [])}
    identifiers = product_index.get("identifier_lookup", {})
    normalized_alias_lookup: dict[str, list[str]] = defaultdict(list)
    for alias, product_ids in product_index.get("alias_lookup", {}).items():
        for product_id in product_ids:
            normalized_alias_lookup[normalize_key(alias)].append(product_id)
    entity_by_id = {entity.get("entity_id"): entity for entity in product_index.get("entities", [])}
    for row in rows:
        configured = row.get("product_id", "")
        matches: list[tuple[str, str, dict[str, Any] | None]] = []
        identifier_entity_ids: set[str] = set()
        for field in ("asin", "sku", "jan", "model_number"):
            value = clean_text(row.get(field))
            if value and value in identifiers.get(field, {}):
                for entity_id in identifiers[field][value]:
                    entity = entity_by_id.get(entity_id)
                    if entity:
                        identifier_entity_ids.add(entity_id)
                        matches.append((entity.get("product_id", ""), f"{field}:{value}", entity))
        if configured and configured in products:
            matches.append((configured, "configured_product_id", None))
        if not matches:
            for value in (row.get("channel_product_name", ""), row.get("variant_text", "")):
                ids = normalized_alias_lookup.get(normalize_key(value), [])
                for product_id in ids:
                    matches.append((product_id, f"exact_alias:{value}", None))
        product_ids = sorted({match[0] for match in matches if match[0]})
        if len(identifier_entity_ids) > 1:
            row["mapping_status"] = "Conflicting"
            row["mapping_basis"] = "Identifier maps to multiple entities: " + ", ".join(sorted(identifier_entity_ids))
            row["manual_review_required"] = "Yes"
        elif len(product_ids) == 1:
            row["product_id"] = product_ids[0]
            row["mapping_status"] = "Confirmed"
            row["mapping_basis"] = "; ".join(sorted({match[1] for match in matches}))
            entities = [match[2] for match in matches if match[2]]
            variant_ids = sorted({entity.get("variant_id", "") for entity in entities if entity.get("variant_id")})
            bundle_ids = sorted({entity.get("bundle_id", "") for entity in entities if entity.get("bundle_id")})
            if len(variant_ids) == 1:
                row["variant_id"] = variant_ids[0]
            if len(bundle_ids) == 1:
                row["bundle_id"] = bundle_ids[0]
        elif len(product_ids) > 1:
            row["mapping_status"] = "Conflicting"
            row["mapping_basis"] = "Multiple exact matches: " + ", ".join(product_ids)
            row["manual_review_required"] = "Yes"
        else:
            row["mapping_status"] = "Unmapped"
            row["mapping_basis"] = "No exact Product Knowledge match"
            row["manual_review_required"] = "Yes"
        bundle_clues = ("顔認証", "指紋認証", "キーパッド", "セット")
        bundle_url_clues = ("keypadvision", "keypad", "vision-pro", "vision_combo")
        if (
            row.get("mapping_status") == "Confirmed"
            and not row.get("bundle_id")
            and (
                any(clue in row.get("variant_text", "") for clue in bundle_clues)
                or any(clue in row.get("review_url", "").casefold() for clue in bundle_url_clues)
            )
        ):
            row["mapping_status"] = "Probable"
            row["mapping_basis"] = f"{row.get('mapping_basis')}; unresolved_bundle_or_accessory"
            row["manual_review_required"] = "Yes"
    return rows


def classify_rows(
    rows: list[dict[str, str]],
    sentiment_rules: dict[str, Any],
    taxonomy: dict[str, Any],
) -> list[dict[str, str]]:
    positives = [clean_text(item) for item in sentiment_rules.get("positive", [])]
    negatives = [clean_text(item) for item in sentiment_rules.get("negative", [])]
    contrasts = [clean_text(item) for item in sentiment_rules.get("contrast_markers", [])]
    recoveries = [clean_text(item) for item in sentiment_rules.get("recovery_markers", [])]
    critical_terms = [clean_text(item) for item in sentiment_rules.get("critical", [])]
    high_terms = [clean_text(item) for item in sentiment_rules.get("high", [])]
    topics = taxonomy.get("topics", {})
    for row in rows:
        text = f"{row.get('review_title', '')} {row.get('review_body', '')}"
        positive_hits = [item for item in positives if item and item in text]
        negative_hits = [item for item in negatives if item and item in text]
        contrast_hits = [item for item in contrasts if item and item in text]
        recovery_hits = [item for item in recoveries if item and item in text]
        confidence = "High" if len(text) >= 25 else "Medium" if text else "Low"
        if positive_hits and negative_hits:
            sentiment = "Mixed"
        elif negative_hits and recovery_hits:
            sentiment = "Mixed"
        elif positive_hits:
            sentiment = "Positive"
        elif negative_hits:
            sentiment = "Negative"
        else:
            rating = float(row["rating"]) if row.get("rating") else None
            if rating is None:
                sentiment = "Neutral"
            elif rating >= 4:
                sentiment = "Positive"
            elif rating <= 2:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
            confidence = "Low"
        score = {"Positive": 1, "Neutral": 0, "Negative": -1, "Mixed": 0}[sentiment]
        topic_hits: list[str] = []
        for topic, config in topics.items():
            if any(clean_text(keyword) in text for keyword in config.get("keywords", []) if clean_text(keyword)):
                topic_hits.append(topic)
        primary = topic_hits[0] if topic_hits else ("Positive Experience" if sentiment == "Positive" else "Other")
        severity = "Low"
        if any(term in text for term in critical_terms if term):
            severity = "Critical"
        elif any(term in text for term in high_terms if term):
            severity = "High"
        elif sentiment in {"Negative", "Mixed"}:
            severity = "Medium"
        manual = row.get("manual_review_required") == "Yes"
        if severity in {"Critical", "High"} or confidence == "Low" or sentiment == "Mixed":
            manual = True
        if contrast_hits and not recovery_hits:
            manual = True
        owner = clean_text((topics.get(primary) or {}).get("owner")) or "Product"
        row.update({
            "sentiment": sentiment,
            "sentiment_score": str(score),
            "primary_topic": primary,
            "secondary_topics": "; ".join(topic_hits[1:]),
            "issue_category": primary if sentiment in {"Negative", "Mixed"} else "",
            "praised_feature": primary if sentiment in {"Positive", "Mixed"} else "",
            "complained_feature": primary if sentiment in {"Negative", "Mixed"} else "",
            "severity": severity,
            "analysis_confidence": confidence,
            "classification_basis": json.dumps({
                "positive_hits": positive_hits,
                "negative_hits": negative_hits,
                "contrast_hits": contrast_hits,
                "recovery_hits": recovery_hits,
                "topic_hits": topic_hits,
            }, ensure_ascii=False, sort_keys=True),
            "manual_review_required": "Yes" if manual else "No",
            "responsibility_owner": owner,
            "return_intent": "Yes" if any(term in text for term in ("返品", "返金")) else row.get("return_intent", "Unknown"),
            "support_contacted": "Yes" if any(term in text for term in ("サポート", "問い合わせ", "カスタマーサービス", "連絡しました")) else row.get("support_contacted", "Unknown"),
            "installation_related": "Yes" if primary == "Installation" else "No",
            "app_related": "Yes" if primary == "App" else "No",
            "hardware_related": "Yes" if primary in {"Product Quality", "Battery", "Noise"} else "No",
            "logistics_related": "Yes" if primary in {"Delivery", "Packaging"} else "No",
        })
        motivations = [term for term in ("子ども", "子供", "家族写真", "ペット", "思い出", "インテリア", "プレゼント", "作品", "模様替え") if term in text]
        scenarios = [term for term in ("リビング", "玄関", "寝室", "壁", "卓上", "オフィス", "店舗", "子ども部屋") if term in text]
        gaps = [term for term in ("暗い", "見づらい", "発色", "10枚", "高い", "高額", "思っていた", "想像と違う") if term in text]
        row["purchase_motivation"] = "; ".join(motivations)
        row["usage_scenario"] = "; ".join(scenarios)
        row["expectation_gap"] = "; ".join(gaps)
        row["issue_subcategory"] = "; ".join(topic_hits[:3]) if sentiment in {"Negative", "Mixed"} else ""
        row["firmware_related"] = "Yes" if any(term in text for term in ("ファームウェア", "アップデート", "更新後")) else "No"
        row["installation_related"] = "Yes" if any(term in text for term in ("設置", "壁掛け", "フック", "取付", "取り付け", "額縁")) else row["installation_related"]
        row["app_related"] = "Yes" if any(term in text for term in ("アプリ", "アップロード", "同期", "転送", "クラウド", "ローカル", "スライドショー")) else row["app_related"]
        row["hardware_related"] = "Yes" if any(term in text for term in ("暗い", "発色", "画質", "解像度", "画面", "ディスプレイ", "充電", "バッテリー")) else row["hardware_related"]
    return rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def assign_duplicates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_source_id: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("source_review_id"):
            by_source_id[(row.get("source", ""), row["source_review_id"])].append(row)
        by_hash[row.get("original_review_hash", "")].append(row)
    for group in by_source_id.values():
        if len(group) > 1:
            group_id = f"dup_{sha256_text('|'.join(sorted(row['review_id'] for row in group)))[:16]}"
            canonical = sorted(row["review_id"] for row in group)[0]
            for row in group:
                row.update({"duplicate_type": "Exact Duplicate", "duplicate_group_id": group_id, "canonical_review_id": canonical})
    for group in by_hash.values():
        if len(group) < 2:
            continue
        sources = {row.get("source") for row in group}
        variants = {row.get("variant_id") for row in group}
        duplicate_type = "Cross-Channel Duplicate" if len(sources) > 1 else "Cross-Variant Duplicate" if len(variants) > 1 else "Suspected Duplicate"
        group_id = f"dup_{sha256_text('|'.join(sorted(row['review_id'] for row in group)))[:16]}"
        canonical = sorted(row["review_id"] for row in group)[0]
        for row in group:
            if not row.get("duplicate_type"):
                row.update({"duplicate_type": duplicate_type, "duplicate_group_id": group_id, "canonical_review_id": canonical})
                if duplicate_type == "Suspected Duplicate":
                    row["manual_review_required"] = "Yes"
    return rows


def merge_incremental(workspace: Path, incoming: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]]:
    reviews_path = workspace / "normalized" / "reviews.csv"
    versions_path = workspace / "normalized" / "review_versions.csv"
    existing_rows = read_csv_rows(reviews_path)
    for row in existing_rows:
        row["source_url"] = row.get("source_url") or row.get("review_url") or row.get("channel_product_url", "")
    existing = {
        row["review_id"]: row
        for row in existing_rows
        if row.get("review_id")
    }
    versions = read_csv_rows(versions_path)
    for row in versions:
        row["source_url"] = row.get("source_url") or row.get("review_url") or row.get("channel_product_url", "")
    version_ids = {row.get("version_id") for row in versions}
    counts = {"new": 0, "updated": 0, "unchanged": 0}
    for row in incoming:
        old = existing.get(row["review_id"])
        if old is None:
            counts["new"] += 1
            existing[row["review_id"]] = row
            if row["version_id"] not in version_ids:
                versions.append(dict(row))
                version_ids.add(row["version_id"])
        elif old.get("original_review_hash") != row.get("original_review_hash"):
            counts["updated"] += 1
            row["review_status"] = "Updated"
            existing[row["review_id"]] = row
            if row["version_id"] not in version_ids:
                versions.append(dict(row))
                version_ids.add(row["version_id"])
        else:
            counts["unchanged"] += 1
            old["last_checked_at"] = row.get("last_checked_at", old.get("last_checked_at", ""))
            old["coverage_status"] = row.get("coverage_status", old.get("coverage_status", ""))
            for field in (
                "variant_id", "bundle_id", "mapping_status", "mapping_basis",
                "sentiment", "sentiment_score", "primary_topic", "secondary_topics",
                "issue_category", "issue_subcategory", "purchase_motivation",
                "usage_scenario", "praised_feature", "complained_feature",
                "expectation_gap", "severity", "return_intent", "support_contacted",
                "firmware_related", "installation_related", "app_related",
                "hardware_related", "logistics_related", "analysis_confidence",
                "classification_basis", "manual_review_required",
                "responsibility_owner", "notes", "source_url",
            ):
                if field in row:
                    old[field] = row.get(field, "")
    canonical = assign_duplicates(list(existing.values()))
    write_csv_rows(reviews_path, canonical, REVIEW_COLUMNS)
    write_csv_rows(versions_path, versions, REVIEW_COLUMNS)
    try:
        import pandas as pd
        pd.DataFrame(canonical, columns=REVIEW_COLUMNS).to_parquet(workspace / "normalized" / "reviews.parquet", index=False)
    except Exception:
        pass
    return canonical, versions, counts


def validate_rows(rows: list[dict[str, str]], product_index: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    known_products = {item.get("product_id") for item in product_index.get("products", [])}
    seen: set[str] = set()
    for number, row in enumerate(rows, 2):
        def add(code: str, severity: str, message: str) -> None:
            issues.append({"row": str(number), "review_id": row.get("review_id", ""), "severity": severity, "code": code, "message": message})
        if not row.get("review_id"):
            add("REVIEW_ID_MISSING", "Critical", "review_id is required")
        elif row["review_id"] in seen:
            add("REVIEW_ID_DUPLICATE", "Critical", "review_id must be unique in canonical reviews")
        seen.add(row.get("review_id", ""))
        if row.get("rating"):
            rating = float(row["rating"])
            if not 0 <= rating <= 5:
                add("RATING_INVALID", "Critical", "rating must be between 0 and 5")
        if row.get("sentiment") not in SENTIMENTS:
            add("SENTIMENT_INVALID", "Critical", "sentiment enum is invalid")
        if row.get("severity") not in SEVERITIES:
            add("SEVERITY_INVALID", "Critical", "severity enum is invalid")
        if row.get("mapping_status") not in MAPPING_STATUSES:
            add("MAPPING_STATUS_INVALID", "Critical", "mapping_status enum is invalid")
        elif row.get("mapping_status") == "Probable":
            add("MAPPING_REVIEW_REQUIRED", "High", "variant or bundle mapping is not confirmed")
        elif row.get("mapping_status") == "Unmapped":
            add("PRODUCT_UNMAPPED", "High", "record is not mapped to an exact Product Knowledge entity")
        elif row.get("mapping_status") == "Conflicting":
            add("PRODUCT_MAPPING_CONFLICT", "Critical", "identifiers or exact matches conflict")
        if row.get("review_status") not in REVIEW_STATUSES:
            add("REVIEW_STATUS_INVALID", "Critical", "review_status enum is invalid")
        if row.get("coverage_status") not in COVERAGE_STATUSES:
            add("COVERAGE_STATUS_INVALID", "Critical", "coverage_status enum is invalid")
        if row.get("review_date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("review_date", "")):
            add("REVIEW_DATE_INVALID", "High", "review_date must use YYYY-MM-DD")
        if row.get("product_id") and row.get("product_id") not in known_products:
            add("PRODUCT_UNKNOWN", "Critical", "product_id does not exist in Product Knowledge")
        if not row.get("review_url"):
            add("SOURCE_URL_MISSING", "High", "review_url is required for traceability")
        if not row.get("source_url"):
            add("SOURCE_URL_MISSING", "High", "source_url is required by the data contract")
        if not row.get("review_body"):
            add("REVIEW_BODY_MISSING", "High", "empty text remains Incomplete")
        if row.get("manual_review_required") not in {"Yes", "No"}:
            add("MANUAL_REVIEW_ENUM_INVALID", "Critical", "manual_review_required must be Yes or No")
    return issues


def build_index(rows: list[dict[str, str]], manifest: dict[str, Any], counts: dict[str, int]) -> dict[str, Any]:
    coverage = manifest.get("coverage", [])
    required_incomplete = any(item.get("required") and item.get("coverage_status") not in {"Complete", "Zero Confirmed"} for item in coverage)
    return {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "batch_id": manifest.get("batch_id", ""),
        "status": "Partial" if required_incomplete else "Complete",
        "record_count": len(rows),
        "natural_voc_count": sum(
            row.get("voc_eligibility") == "Natural VOC"
            and row.get("mapping_status") == "Confirmed"
            and row.get("review_status") in {"Active", "Updated"}
            and (not row.get("canonical_review_id") or row.get("canonical_review_id") == row.get("review_id"))
            for row in rows
        ),
        "manual_review_count": sum(row.get("manual_review_required") == "Yes" for row in rows),
        "incremental": counts,
        "coverage": coverage,
        "by_product": dict(Counter(row.get("product_id") or "Unmapped" for row in rows)),
        "by_source": dict(Counter(row.get("source") or "Unknown" for row in rows)),
        "by_sentiment": dict(Counter(row.get("sentiment") or "Unknown" for row in rows)),
    }


def write_reports(
    workspace: Path,
    rows: list[dict[str, str]],
    manifest: dict[str, Any],
    counts: dict[str, int],
    issues: list[dict[str, str]],
    template_path: Path,
    output_dir: Path | None = None,
    persist_state: bool = True,
) -> dict[str, Path]:
    output = output_dir or workspace / "outputs"
    output.mkdir(parents=True, exist_ok=True)
    index = build_index(rows, manifest, counts)
    index_path = workspace / "normalized" / "review_index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coverage = manifest.get("coverage", [])
    coverage_lines = [
        f"| {item.get('product_id')} | {item.get('source')} | {item.get('coverage_status')} | {item.get('records')} | {item.get('failure_reason') or item.get('pagination_boundary')} |"
        for item in coverage
    ]
    collection_report = "\n".join([
        "# Collection Report", "",
        f"- Batch: {manifest.get('batch_id', '')}",
        f"- Status: {index['status']}",
        f"- New: {counts.get('new', 0)}",
        f"- Updated: {counts.get('updated', 0)}",
        f"- Unchanged: {counts.get('unchanged', 0)}",
        "", "| Product | Source | Coverage | Records | Boundary / Failure |",
        "|---|---|---|---:|---|", *coverage_lines, "",
    ])
    (output / "collection_report.md").write_text(collection_report, encoding="utf-8")
    quality_lines = [f"- [{item['severity']}] `{item['code']}` row {item['row']} {item['review_id']}: {item['message']}" for item in issues]
    coverage_gaps = [
        item for item in coverage
        if item.get("required") and item.get("coverage_status") not in {"Complete", "Zero Confirmed"}
    ]
    (output / "data_quality_report.md").write_text(
        "\n".join([
            "# Data Quality Report", "",
            f"- Critical row issues: {sum(item['severity'] == 'Critical' for item in issues)}",
            f"- High row issues: {sum(item['severity'] == 'High' for item in issues)}",
            f"- Required source coverage gaps: {len(coverage_gaps)}",
            "", "## Row Findings", "", *(quality_lines or ["- No row-level findings."]),
            "", "## Coverage Gaps", "",
            *([
                f"- [Data Gap] {item.get('product_id')} / {item.get('source')}: {item.get('coverage_status')} — {item.get('failure_reason') or item.get('pagination_boundary')}"
                for item in coverage_gaps
            ] or ["- No required coverage gaps."]),
            "",
        ]),
        encoding="utf-8",
    )
    duplicates = [row for row in rows if row.get("duplicate_type")]
    write_csv_rows(output / "duplicate_report.csv", duplicates, REPORT_COLUMNS)
    (output / "duplicate_report.md").write_text(
        "\n".join(["# Duplicate Report", "", f"- Duplicate or suspected records: {len(duplicates)}", ""] + [
            f"- {row['review_id']}: {row['duplicate_type']} / {row['duplicate_group_id']}" for row in duplicates
        ]) + "\n",
        encoding="utf-8",
    )
    unmapped = [row for row in rows if row.get("mapping_status") != "Confirmed"]
    (output / "unmapped_products.md").write_text(
        "\n".join(["# Unmapped Products", "", "| Source name | URL | Candidate | Confidence | Reason |", "|---|---|---|---|---|"] + [
            f"| {row.get('channel_product_name') or row.get('source')} | {row.get('channel_product_url') or row.get('review_url')} | {row.get('product_id') or 'Unmapped'} | {row.get('mapping_status')} | {row.get('mapping_basis')} |"
            for row in unmapped
        ]) + "\n",
        encoding="utf-8",
    )
    manual = [row for row in rows if row.get("manual_review_required") == "Yes"]
    write_csv_rows(workspace / "reports" / "manual_review" / "manual_review_queue.csv", manual, REPORT_COLUMNS)
    natural = [
        row for row in rows
        if row.get("voc_eligibility") == "Natural VOC"
        and row.get("mapping_status") == "Confirmed"
        and row.get("review_status") in {"Active", "Updated"}
        and (not row.get("canonical_review_id") or row.get("canonical_review_id") == row.get("review_id"))
    ]
    decisions = [{
        "review_id": row.get("review_id"), "sentiment": row.get("sentiment"),
        "primary_topic": row.get("primary_topic"), "severity": row.get("severity"),
        "confidence": row.get("analysis_confidence"), "basis": json.loads(row.get("classification_basis") or "{}"),
        "manual_review_required": row.get("manual_review_required"),
    } for row in rows]
    (output / "classification_decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    risk_rows = [row for row in natural if row.get("sentiment") in {"Negative", "Mixed"} or row.get("severity") in {"High", "Critical"} or row.get("return_intent") == "Yes"]
    write_csv_rows(output / "risk_queue.csv", risk_rows, REPORT_COLUMNS)
    positive_topics = Counter(row.get("primary_topic") for row in natural if row.get("sentiment") in {"Positive", "Mixed"})
    negative_topics = Counter(row.get("primary_topic") for row in natural if row.get("sentiment") in {"Negative", "Mixed"})
    delta_natural = [
        row for row in natural
        if row.get("batch_id") == manifest.get("batch_id")
    ] if counts.get("new", 0) or counts.get("updated", 0) else []
    delta_positive_topics = Counter(row.get("primary_topic") for row in delta_natural if row.get("sentiment") in {"Positive", "Mixed"})
    delta_negative_topics = Counter(row.get("primary_topic") for row in delta_natural if row.get("sentiment") in {"Negative", "Mixed"})
    action_rows = []
    action_scope = delta_natural or natural
    action_negative_topics = Counter(row.get("primary_topic") for row in action_scope if row.get("sentiment") in {"Negative", "Mixed"})
    for topic, count in action_negative_topics.most_common():
        related = [row for row in action_scope if row.get("primary_topic") == topic and row.get("sentiment") in {"Negative", "Mixed"}]
        max_severity = next((severity for severity in ("Critical", "High", "Medium", "Low") if any(row.get("severity") == severity for row in related)), "Low")
        if count >= 2 or max_severity in {"Critical", "High"}:
            action_rows.append({
                "priority": "P0" if max_severity == "Critical" else "P1" if max_severity == "High" else "P2",
                "action": f"复核并处理 {topic} 相关反馈",
                "problem": f"{count} 条可归因自然 VOC",
                "evidence": "; ".join(row["review_id"] for row in related[:5]),
                "owner": related[0].get("responsibility_owner", "Product"),
                "timing": "Next biweekly review",
                "success_metric": "完成责任判断并记录验证结果",
                "confidence": "High" if count >= 3 else "Medium",
            })
    write_csv_rows(output / "action_plan.csv", action_rows, ["priority", "action", "problem", "evidence", "owner", "timing", "success_metric", "confidence"])
    product_summary: list[dict[str, Any]] = []
    all_products = sorted({item.get("product_id") for item in coverage if item.get("product_id")})
    for product in all_products:
        group = [row for row in natural if row.get("product_id") == product]
        product_coverage = [item for item in coverage if item.get("product_id") == product]
        count_available = bool(group) or any(
            item.get("coverage_status") in {"Complete", "Zero Confirmed"} for item in product_coverage
        )
        product_summary.append({
            "product_id": product,
            "natural_voc": len(group) if count_available else "",
            "positive": sum(row.get("sentiment") == "Positive" for row in group) if count_available else "",
            "neutral": sum(row.get("sentiment") == "Neutral" for row in group) if count_available else "",
            "negative": sum(row.get("sentiment") == "Negative" for row in group) if count_available else "",
            "mixed": sum(row.get("sentiment") == "Mixed" for row in group) if count_available else "",
            "manual_review": sum(row.get("manual_review_required") == "Yes" for row in group) if count_available else "",
            "coverage_note": "; ".join(
                f"{item.get('source')}={item.get('coverage_status')}" for item in product_coverage
            ) or "Not Available",
        })
    write_csv_rows(
        output / "product_summary.csv", product_summary,
        ["product_id", "natural_voc", "positive", "neutral", "negative", "mixed", "manual_review", "coverage_note"],
    )
    channel_summary: list[dict[str, Any]] = []
    for item in sorted(coverage, key=lambda row: (row.get("product_id", ""), row.get("source", ""))):
        product, source = item.get("product_id", ""), item.get("source", "")
        group = [row for row in natural if row.get("product_id") == product and row.get("source") == source]
        product_sources_with_records = {
            row.get("source") for row in natural if row.get("product_id") == product
        }
        product_coverage = {
            row.get("source"): row.get("coverage_status")
            for row in coverage if row.get("product_id") == product
        }
        source_windows = {}
        for source_name in product_sources_with_records:
            dates = sorted(
                row.get("review_date", "") for row in natural
                if row.get("product_id") == product
                and row.get("source") == source_name
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("review_date", ""))
            )
            source_windows[source_name] = (dates[0], dates[-1]) if dates else ("", "")
        comparable = (
            len(product_sources_with_records) >= 2
            and all(product_coverage.get(source_name) == "Complete" for source_name in product_sources_with_records)
            and len(set(source_windows.values())) == 1
            and all(
                sum(row.get("product_id") == product and row.get("source") == source_name for row in natural) >= 5
                for source_name in product_sources_with_records
            )
        )
        dates = sorted(
            row.get("review_date", "") for row in group
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("review_date", ""))
        )
        count_available = bool(group) or item.get("coverage_status") in {"Complete", "Zero Confirmed"}
        channel_summary.append({
            "product_id": product,
            "source": source,
            "coverage_status": item.get("coverage_status"),
            "natural_voc": len(group) if count_available else "",
            "positive": sum(row.get("sentiment") == "Positive" for row in group) if count_available else "",
            "negative": sum(row.get("sentiment") == "Negative" for row in group) if count_available else "",
            "mixed": sum(row.get("sentiment") == "Mixed" for row in group) if count_available else "",
            "analysis_window": f"{dates[0]}..{dates[-1]}" if dates else "Not Available",
            "comparison_status": "Comparable" if comparable else "Not Comparable",
            "data_gap_reason": item.get("failure_reason") or item.get("pagination_boundary"),
        })
    write_csv_rows(
        output / "channel_comparison.csv", channel_summary,
        ["product_id", "source", "coverage_status", "natural_voc", "positive", "negative", "mixed", "analysis_window", "comparison_status", "data_gap_reason"],
    )
    unit_types = {
        "amazon_jp": "review", "rakuten": "review", "yahoo_shopping": "review",
        "switchbot_official": "review", "x": "post", "youtube": "video/comment",
        "media": "article", "specified_links": "link",
    }
    next_steps = {
        "amazon_jp": "User-authorized browser capture; traverse exact ASIN review pages and reconcile IDs/counts",
        "x": "User-authorized browser capture with screenshots and resume IDs; status remains Partial",
        "youtube": "User-authorized browser capture; fixed video list, scroll to end and expand every reply",
    }
    unified_rows = []
    for item in sorted(coverage, key=lambda row: row.get("source", "")):
        source = item.get("source", "")
        source_rows = [row for row in rows if row.get("source") == source]
        observed = item.get("records", "")
        declared_raw = item.get("declared_records", "")
        declared = declared_raw if unit_types.get(source) == "review" else ""
        try:
            coverage_rate = f"{float(observed) / float(declared):.1%}" if unit_types.get(source) == "review" and float(declared) > 0 else ""
        except (TypeError, ValueError, ZeroDivisionError):
            coverage_rate = ""
        natural_count = sum(
            row.get("voc_eligibility") == "Natural VOC"
            and row.get("review_status") in {"Active", "Updated"}
            and (not row.get("canonical_review_id") or row.get("canonical_review_id") == row.get("review_id"))
            for row in source_rows
        )
        unified_rows.append({
            "source": source,
            "unit_type": unit_types.get(source, "record"),
            "observed_units": observed,
            "declared_total": declared,
            "raw_records": len(source_rows),
            "analyzable_records": sum(row.get("review_status") in {"Active", "Updated"} and bool(row.get("review_body")) for row in source_rows),
            "natural_voc": natural_count,
            "context_only": sum(row.get("voc_eligibility") == "Context Only" for row in source_rows),
            "incomplete": sum(row.get("review_status") == "Incomplete" for row in source_rows),
            "coverage_rate": coverage_rate,
            "coverage_status": item.get("coverage_status", ""),
            "comparison_status": next((row.get("comparison_status", "Not Comparable") for row in channel_summary if row.get("source") == source), "Not Comparable"),
            "denominator_note": "Displayed platform total; may include rating-only or shared-variant records" if source == "amazon_jp" else item.get("pagination_boundary", ""),
            "next_step": next_steps.get(source, "No remediation required" if item.get("coverage_status") in {"Complete", "Zero Confirmed"} else "Complete configured scope"),
        })
    unified_columns = ["source", "unit_type", "observed_units", "declared_total", "raw_records", "analyzable_records", "natural_voc", "context_only", "incomplete", "coverage_rate", "coverage_status", "comparison_status", "denominator_note", "next_step"]
    write_csv_rows(output / "unified_channel_statistics.csv", unified_rows, unified_columns)
    remediation = [row for row in unified_rows if row["source"] in {"amazon_jp", "x", "youtube"}]
    (output / "channel_remediation_plan.md").write_text("\n".join([
        "# Channel Remediation Plan", "",
        "统一口径：Observed Units 是已看到的平台内容单元；Natural VOC 只统计有正文、已映射且非付费/官方/转载的用户反馈；不同 unit_type 不直接相加为评论总量。", "",
        "| Channel | Current | Observed | Declared | Natural VOC | Required remediation |",
        "|---|---|---:|---:|---:|---|",
        *(f"| {r['source']} | {r['coverage_status']} | {r['observed_units']} | {r['declared_total'] or 'Not Available'} | {r['natural_voc']} | {r['next_step']} |" for r in remediation),
        "", "## Completion gates", "",
        "- Amazon Japan: all three ASIN review scopes must be traversed in an authorized Brand Customer Reviews session or supplied as user evidence; record every page and reconcile to the displayed scope total.",
        "- X: use one fixed query registry, UTC date boundaries, and continue `next_token` until absent for every query/date slice.",
        "- YouTube: enumerate the fixed video set, exhaust `commentThreads.list`, and call `comments.list` whenever replies are not fully embedded.",
        "- A channel remains Partial if credentials, permissions, pagination tokens, or any page fail.", "",
    ]), encoding="utf-8")
    trend_groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in natural:
        month = clean_text(row.get("review_date"))[:7] if re.match(r"\d{4}-\d{2}", clean_text(row.get("review_date"))) else "Unknown"
        trend_groups[(month, row.get("product_id", ""), row.get("source", ""))].append(row)
    trend_rows = [{
        "month": month,
        "product_id": product,
        "source": source,
        "natural_voc": len(group),
        "positive": sum(row.get("sentiment") == "Positive" for row in group),
        "negative": sum(row.get("sentiment") == "Negative" for row in group),
        "mixed": sum(row.get("sentiment") == "Mixed" for row in group),
        "trend_confidence": "Low" if index["status"] == "Partial" else "Medium",
    } for (month, product, source), group in sorted(trend_groups.items())]
    write_csv_rows(
        output / "trend_analysis.csv", trend_rows,
        ["month", "product_id", "source", "natural_voc", "positive", "negative", "mixed", "trend_confidence"],
    )
    focus_counts = {
        "installation": sum(r.get("installation_related") == "Yes" for r in natural),
        "app": sum(r.get("app_related") == "Yes" for r in natural),
        "hardware": sum(r.get("hardware_related") == "Yes" for r in natural),
        "return": sum(r.get("return_intent") == "Yes" for r in natural),
        "competitor": sum("Competitor Comparison" in (r.get("primary_topic", "") + ";" + r.get("secondary_topics", "")) for r in natural),
    }
    summary_md = "\n".join([
        "# Executive Summary", "",
        f"- [Fact] 本次首次全量批次累计 {len(natural)} 条可计入 Natural VOC，{len(risk_rows)} 条进入风险队列；总体状态为 {index['status']}。",
        f"- [Fact] 重点相关记录：安装 {focus_counts['installation']}、App {focus_counts['app']}、硬件/显示 {focus_counts['hardware']}、退货 {focus_counts['return']}、竞品比较 {focus_counts['competitor']}。",
        f"- [Insight] 主要负向主题：{', '.join(f'{k} ({v})' for k,v in negative_topics.most_common(5)) or 'Not Available'}。",
        "- [Hypothesis] 显示亮度/发色与内容容量的预期差，可能同时影响满意度和退货风险；需结合退货原因与客服工单验证。",
        "- [Recommendation] 在商品页首屏明确环境光、电子纸观感和本地轮播容量；App 团队复核上传/同步与轮播限制；安装说明按三种尺寸拆分。",
        "- [Data Gap] Amazon、YouTube 评论、X 历史和媒体范围未完成，任何缺失不得解释为零或问题消失。", "",
    ])
    (output / "executive_summary.md").write_text(summary_md, encoding="utf-8")
    (output / "full_analysis.md").write_text(summary_md + "\n## Evidence Layers\n\n" + "\n".join([
        f"- [Fact] {k}: {v} 条" for k,v in negative_topics.most_common(10)
    ]) + "\n\n## Channel Note\n\n- [Insight] 渠道比较只呈现观测样本；不同时间窗或 Partial 渠道标记 Not Comparable。\n", encoding="utf-8")
    product_rows = "".join(
        f"<tr><td>{html.escape(product)}</td><td>{count}</td><td>{sum(1 for row in natural if row.get('product_id') == product and row.get('sentiment') == 'Negative')}</td><td>{sum(1 for row in natural if row.get('product_id') == product and row.get('manual_review_required') == 'Yes')}</td></tr>"
        for product, count in Counter(row.get("product_id") or "Unmapped" for row in natural).items()
    ) or "<tr><td colspan='4'>No confirmed Natural VOC records.</td></tr>"
    coverage_rows = "".join(
        f"<tr><td>{html.escape(str(item.get('product_id')))}</td><td>{html.escape(str(item.get('source')))}</td><td>{html.escape(str(item.get('coverage_status')))}</td><td>{html.escape(str(item.get('failure_reason') or item.get('pagination_boundary')))}</td></tr>"
        for item in coverage
    )
    unified_html_rows = "".join(
        f"<tr><td>{html.escape(str(r['source']))}</td><td>{html.escape(str(r['unit_type']))}</td><td>{r['observed_units']}</td><td>{r['declared_total'] or 'N/A'}</td><td>{r['analyzable_records']}</td><td>{r['natural_voc']}</td><td>{r['context_only']}</td><td>{r['incomplete']}</td><td>{html.escape(str(r['coverage_status']))}</td></tr>"
        for r in unified_rows
    )
    body = f"""
<header><h1>Customer Review Intelligence</h1><div class="muted">Batch {html.escape(str(index['batch_id']))} · Status {index['status']}</div></header>
<section class="grid">
  <div class="metric"><span class="muted">All records</span><strong>{len(rows)}</strong></div>
  <div class="metric"><span class="muted">Natural VOC</span><strong>{len(natural)}</strong></div>
  <div class="metric"><span class="muted">Manual review</span><strong>{len(manual)}</strong></div>
  <div class="metric"><span class="muted">Data issues</span><strong>{len(issues)}</strong></div>
</section>
<section class="panel"><h2>Executive Summary</h2>
<p><b>[Fact]</b> 累计确认 {len(natural)} 条已映射 Natural VOC；本批次确认 delta {len(delta_natural)} 条，其中新增 {counts.get('new', 0)} 条，更新 {counts.get('updated', 0)} 条。</p>
<p><b>[Data Gap]</b> 运行状态为 {index['status']}。未完成来源不得解释为零评论或问题消失。</p></section>
<section class="panel"><h2>Product Overview</h2><table><thead><tr><th>Product</th><th>Natural VOC</th><th>Negative</th><th>Manual Review</th></tr></thead><tbody>{product_rows}</tbody></table></section>
<section class="panel"><h2>Top Drivers</h2><p><span class="good">Positive:</span> {html.escape(', '.join(f'{k} ({v})' for k,v in positive_topics.most_common(5)) or 'Not Available')}</p><p><span class="bad">Negative:</span> {html.escape(', '.join(f'{k} ({v})' for k,v in negative_topics.most_common(5)) or 'Not Available')}</p></section>
<section class="panel"><h2>Priority Risk Queue</h2><p><b>[Fact]</b> {len(risk_rows)} Natural VOC records require negative/mixed or severity review.</p><p>Installation {focus_counts['installation']} · App {focus_counts['app']} · Hardware/display {focus_counts['hardware']} · Return {focus_counts['return']} · Competitor {focus_counts['competitor']}</p></section>
<section class="panel"><h2>Unified Channel Statistics</h2><p><b>[Fact]</b> 不同渠道的内容单元不同；视频、帖子和评论不得直接合计为“评论总数”。</p><table><thead><tr><th>Source</th><th>Unit</th><th>Observed</th><th>Declared</th><th>Analyzable</th><th>Natural VOC</th><th>Context</th><th>Incomplete</th><th>Status</th></tr></thead><tbody>{unified_html_rows}</tbody></table></section>
<section class="panel"><h2>Source Coverage</h2><table><thead><tr><th>Product</th><th>Source</th><th>Status</th><th>Boundary / Failure</th></tr></thead><tbody>{coverage_rows}</tbody></table></section>
"""
    template = template_path.read_text(encoding="utf-8")
    html_path = output / "latest_review_summary.html"
    html_path.write_text(template.replace("{{TITLE}}", "Customer Review Intelligence").replace("{{BODY}}", body), encoding="utf-8")
    biweekly = "\n".join([
        "# Customer Review Intelligence Biweekly Report",
        "",
        f"- Batch: {index['batch_id']}",
        f"- Status: {index['status']}",
        f"- [Fact] Confirmed Natural VOC (cumulative): {len(natural)}",
        f"- [Fact] Confirmed Natural VOC (current delta): {len(delta_natural)}",
        f"- [Fact] Delta: new {counts.get('new', 0)}, updated {counts.get('updated', 0)}, unchanged {counts.get('unchanged', 0)}",
        f"- [Data Gap] Required incomplete source pairs: {sum(item.get('required') and item.get('coverage_status') not in {'Complete', 'Zero Confirmed'} for item in coverage)}",
        "",
        "## Core Findings",
        "",
        f"- [Insight] Delta positive topics: {', '.join(f'{key} ({value})' for key, value in delta_positive_topics.most_common(5)) or 'Not Available'}",
        f"- [Insight] Delta negative topics: {', '.join(f'{key} ({value})' for key, value in delta_negative_topics.most_common(5)) or 'Not Available'}",
        "- [Hypothesis] Topic frequencies may reflect first-page and channel coverage, not market-wide prevalence.",
        "",
        "## Recommendations",
        "",
        *(f"- [Recommendation] {row['action']} / Owner: {row['owner']} / Timing: {row['timing']} / Metric: {row['success_metric']}" for row in action_rows),
        *(["- [Recommendation] Continue collection; no repeated high-risk issue met the action threshold."] if not action_rows else []),
        "",
    ])
    report_dir = workspace / "reports" / "biweekly"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{index['batch_id']}.md"
    report_path.write_text(biweekly, encoding="utf-8")
    (report_dir / "latest.md").write_text(biweekly, encoding="utf-8")
    if persist_state:
        state_dir = workspace / "state"
        history_dir = state_dir / "runs"
        history_dir.mkdir(parents=True, exist_ok=True)
        review_dates = sorted(row.get("review_date", "") for row in rows if re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("review_date", "")))
        state_payload = {
            "schema_version": "1.0",
            "batch_id": index["batch_id"],
            "completed_at": index["generated_at"],
            "collection_cutoff": manifest.get("collected_at", index["generated_at"]),
            "review_date_cutoff": review_dates[-1] if review_dates else "",
            "status": index["status"],
            "record_count": len(rows),
            "delta_record_count": len(delta_natural),
            "incremental": counts,
            "prior_success_batch": (manifest.get("requested_window") or {}).get("prior_success_batch", ""),
        }
        (state_dir / "last_success.json").write_text(
            json.dumps(state_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (history_dir / f"{index['batch_id']}.json").write_text(
            json.dumps(state_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return {
        "index": index_path,
        "collection": output / "collection_report.md",
        "quality": output / "data_quality_report.md",
        "biweekly": report_path,
        "html": html_path,
        "executive_summary": output / "executive_summary.md",
        "full_analysis": output / "full_analysis.md",
        "risk_queue": output / "risk_queue.csv",
        "unified_channel_statistics": output / "unified_channel_statistics.csv",
        "channel_remediation_plan": output / "channel_remediation_plan.md",
    }
