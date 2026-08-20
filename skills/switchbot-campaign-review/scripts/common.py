#!/usr/bin/env python3
"""Shared utilities for the SwitchBot campaign review pipeline."""

from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

LOGGER = logging.getLogger("switchbot_campaign_review")

SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".tsv", ".json", ".md", ".pdf"}
SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", "node_modules", "_intermediate", "charts"}

CANONICAL_COLUMNS = [
    "date",
    "period",
    "campaign",
    "channel",
    "subchannel",
    "product",
    "product_raw",
    "product_id",
    "budget",
    "spend",
    "impressions",
    "reach",
    "clicks",
    "conversions",
    "revenue",
    "views",
    "engagements",
    "sends",
    "delivered",
    "opens",
    "unsubscribes",
    "ctr",
    "cpc",
    "cpm",
    "cvr",
    "cpa",
    "roas",
    "frequency",
    "vtr",
    "completion_rate",
    "currency",
    "tax_basis",
    "attribution_window",
    "conversion_definition",
    "agency_fee_basis",
]

NUMERIC_COLUMNS = [
    "budget",
    "spend",
    "impressions",
    "reach",
    "clicks",
    "conversions",
    "revenue",
    "views",
    "engagements",
    "sends",
    "delivered",
    "opens",
    "unsubscribes",
    "ctr",
    "cpc",
    "cpm",
    "cvr",
    "cpa",
    "roas",
    "frequency",
    "vtr",
    "completion_rate",
]

RATE_COLUMNS = {"ctr", "cvr", "vtr", "completion_rate"}

ALIASES: dict[str, set[str]] = {
    "date": {"date", "day", "日付", "日期", "日期时间", "日"},
    "period": {"period", "year", "年度", "年份", "campaignyear", "活动年度"},
    "campaign": {"campaign", "campaignname", "キャンペーン", "活动", "活動", "项目", "項目"},
    "channel": {"channel", "platform", "media", "媒体", "渠道", "チャネル"},
    "subchannel": {"subchannel", "placement", "adgroup", "媒体细分", "子渠道", "サブチャネル"},
    "product": {"product", "productname", "sku", "产品", "商品", "製品"},
    "budget": {"budget", "预算", "予算"},
    "spend": {"spend", "cost", "adspend", "消化金额", "花费", "広告費", "費用"},
    "impressions": {"impressions", "impression", "imp", "表示回数", "曝光", "曝光量"},
    "reach": {"reach", "reached", "リーチ", "触达", "覆盖人数"},
    "clicks": {"clicks", "click", "クリック", "点击", "点击量"},
    "conversions": {"conversions", "conversion", "cv", "購入", "转化", "订单", "orders"},
    "revenue": {"revenue", "sales", "gmv", "売上", "销售额", "売上高"},
    "views": {"views", "view", "video views", "再生回数", "播放量", "观看量"},
    "engagements": {"engagements", "engagement", "互动量", "エンゲージメント"},
    "sends": {"sends", "sent", "send", "发送量", "配信数"},
    "delivered": {"delivered", "delivery", "送达量", "配信成功数"},
    "opens": {"opens", "open", "打开量", "開封数"},
    "unsubscribes": {"unsubscribes", "unsubscribe", "退订", "配信停止"},
    "ctr": {"ctr", "clickthroughrate", "点击率", "クリック率"},
    "cpc": {"cpc", "costperclick", "点击成本"},
    "cpm": {"cpm", "costpermille", "千次曝光成本"},
    "cvr": {"cvr", "conversionrate", "转化率", "購入率"},
    "cpa": {"cpa", "costperacquisition", "转化成本", "獲得単価"},
    "roas": {"roas", "广告回报率", "広告費用対効果"},
    "frequency": {"frequency", "freq", "频次", "フリークエンシー"},
    "vtr": {"vtr", "viewthroughrate", "视听率", "視聴率"},
    "completion_rate": {"completionrate", "videocompletionrate", "完播率", "完全視聴率"},
    "currency": {"currency", "币种", "通貨"},
    "tax_basis": {"taxbasis", "tax", "含税口径", "税区分"},
    "attribution_window": {"attributionwindow", "归因窗口", "アトリビューション期間"},
    "conversion_definition": {
        "conversiondefinition",
        "conversiontype",
        "cvdefinition",
        "转化定义",
        "转化口径",
        "コンバージョン定義",
    },
    "agency_fee_basis": {
        "agencyfeebasis",
        "agencyfee",
        "代理费口径",
        "是否含代理费",
        "代理店手数料",
    },
}

CHANNEL_NORMALIZATION = {
    "google": "Google Ads",
    "googleads": "Google Ads",
    "youtubeads": "YouTube Ads",
    "youtube": "YouTube",
    "meta": "Meta Ads",
    "metaads": "Meta Ads",
    "facebookads": "Meta Ads",
    "yahooads": "Yahoo Ads",
    "amazonads": "Amazon Ads",
    "smartnews": "SmartNews",
    "line": "LINE",
    "edm": "EDM",
    "email": "EDM",
    "apppush": "App Push",
    "push": "App Push",
    "pr": "PR",
    "kol": "KOL",
    "influencer": "KOL",
    "sns": "SNS",
    "organic": "Organic",
}


@dataclass
class SourceTable:
    source_file: str
    source_table: str
    data: pd.DataFrame
    error: str | None = None


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def normalize_token(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    return re.sub(r"[\s_\-–—/\\().（）【】\[\]:：%]+", "", text)


def build_alias_index(custom_mapping: Mapping[str, str] | None = None) -> dict[str, str]:
    index: dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases | {canonical}:
            index[normalize_token(alias)] = canonical
    if custom_mapping:
        for source, canonical in custom_mapping.items():
            if canonical not in CANONICAL_COLUMNS:
                raise ValueError(f"Unknown canonical field in mapping: {canonical}")
            index[normalize_token(source)] = canonical
    return index


def map_columns(
    frame: pd.DataFrame, custom_mapping: Mapping[str, str] | None = None
) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    alias_index = build_alias_index(custom_mapping)
    mapped: dict[str, str] = {}
    unmapped: list[str] = []
    buckets: dict[str, list[str]] = {}
    for column in frame.columns:
        original = str(column).strip()
        canonical = alias_index.get(normalize_token(original))
        if canonical:
            mapped[original] = canonical
            buckets.setdefault(canonical, []).append(column)
        else:
            unmapped.append(original)

    output = pd.DataFrame(index=frame.index)
    for canonical, source_columns in buckets.items():
        values = frame[source_columns].copy()
        output[canonical] = values.bfill(axis=1).iloc[:, 0]
    for column in frame.columns:
        if str(column).strip() in unmapped:
            safe_name = re.sub(r"\W+", "_", str(column).strip()).strip("_").lower() or "unnamed"
            target = f"extra__{safe_name}"
            suffix = 2
            while target in output.columns:
                target = f"extra__{safe_name}_{suffix}"
                suffix += 1
            output[target] = frame[column]
    return output, mapped, unmapped


def safe_divide(numerator: Any, denominator: Any) -> Any:
    if isinstance(numerator, pd.Series) or isinstance(denominator, pd.Series):
        n = pd.to_numeric(numerator, errors="coerce")
        d = pd.to_numeric(denominator, errors="coerce")
        return n.divide(d.where(d.ne(0)))
    try:
        n = float(numerator)
        d = float(denominator)
    except (TypeError, ValueError):
        return math.nan
    if math.isnan(n) or math.isnan(d) or d == 0:
        return math.nan
    return n / d


def parse_number(value: Any) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return math.nan
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = unicodedata.normalize("NFKC", str(value)).strip()
    if not text or text.lower() in {"nan", "none", "n/a", "na", "-", "—", "not available"}:
        return math.nan
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace(",", "").replace(" ", "")
    text = re.sub(r"^(?:JPY|CNY|RMB|USD|EUR|GBP)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:JPY|CNY|RMB|USD|EUR|GBP)$", "", text, flags=re.IGNORECASE)
    text = text.replace("¥", "").replace("￥", "").replace("$", "").replace("€", "")
    text = text.replace("£", "").replace("円", "").strip()
    try:
        result = float(text.rstrip("%"))
    except ValueError:
        return math.nan
    return -result if negative else result


def parse_markdown_tables(path: Path) -> list[SourceTable]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    tables: list[SourceTable] = []
    current: list[str] = []
    table_index = 0

    def flush() -> None:
        nonlocal table_index, current
        if len(current) < 2:
            current = []
            return
        rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in current]
        if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
            rows.pop(1)
        if len(rows) < 2:
            current = []
            return
        width = len(rows[0])
        rows = [row for row in rows if len(row) == width]
        if len(rows) >= 2:
            table_index += 1
            tables.append(SourceTable(str(path), f"markdown_table_{table_index}", pd.DataFrame(rows[1:], columns=rows[0])))
        current = []

    for line in lines:
        if "|" in line and line.strip().strip("|"):
            current.append(line)
        else:
            flush()
    flush()
    return tables


def read_json_tables(path: Path) -> list[SourceTable]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        return [SourceTable(str(path), "json", pd.json_normalize(payload))]
    if isinstance(payload, dict):
        tables: list[SourceTable] = []
        for key, value in payload.items():
            if isinstance(value, list):
                tables.append(SourceTable(str(path), str(key), pd.json_normalize(value)))
        if tables:
            return tables
        return [SourceTable(str(path), "json", pd.json_normalize(payload))]
    raise ValueError("JSON root must be an object or array")


def read_pdf_tables(path: Path) -> list[SourceTable]:
    import pdfplumber

    tables: list[SourceTable] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table_number, rows in enumerate(page.extract_tables() or [], start=1):
                if not rows or len(rows) < 2:
                    continue
                header = [str(value or f"column_{index + 1}").strip() for index, value in enumerate(rows[0])]
                width = len(header)
                body = [(row + [None] * width)[:width] for row in rows[1:]]
                tables.append(
                    SourceTable(
                        str(path),
                        f"page_{page_number}_table_{table_number}",
                        pd.DataFrame(body, columns=header),
                    )
                )
    return tables


def read_source_file(path: Path) -> list[SourceTable]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".xlsx", ".xls"}:
            workbook = pd.read_excel(path, sheet_name=None)
            return [SourceTable(str(path), str(name), frame) for name, frame in workbook.items()]
        if suffix in {".csv", ".tsv"}:
            separator = "\t" if suffix == ".tsv" else ","
            for encoding in ("utf-8-sig", "utf-8", "cp932"):
                try:
                    frame = pd.read_csv(path, sep=separator, encoding=encoding)
                    return [SourceTable(str(path), path.stem, frame)]
                except UnicodeDecodeError:
                    continue
            raise UnicodeDecodeError("csv", b"", 0, 1, "unsupported encoding")
        if suffix == ".json":
            return read_json_tables(path)
        if suffix == ".md":
            return parse_markdown_tables(path)
        if suffix == ".pdf":
            return read_pdf_tables(path)
    except Exception as exc:
        return [SourceTable(str(path), path.stem, pd.DataFrame(), f"{type(exc).__name__}: {exc}")]
    return []


def discover_source_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    files: list[Path] = []
    for path in input_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        relative_parent_parts = path.relative_to(input_dir).parts[:-1]
        if any(part in SKIP_DIR_NAMES or part == "output" for part in relative_parent_parts):
            continue
        if path.name.lower() in {"expected_output.md", "readme.md"}:
            continue
        files.append(path)
    return sorted(files)


def scan_input_directory(input_dir: Path) -> list[SourceTable]:
    files = discover_source_files(input_dir)
    LOGGER.info("Discovered %d supported source files under %s", len(files), input_dir)
    tables: list[SourceTable] = []
    for path in files:
        file_tables = read_source_file(path)
        LOGGER.info("Read %s: %d table(s)", path.name, len(file_tables))
        tables.extend(file_tables)
    return tables


def inventory_dataframe(tables: Iterable[SourceTable]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for table in tables:
        date_min = date_max = ""
        alias_index = build_alias_index()
        date_columns = [
            column for column in table.data.columns if alias_index.get(normalize_token(column)) == "date"
        ]
        if date_columns and not table.data.empty:
            parsed = pd.to_datetime(table.data[date_columns[0]], errors="coerce")
            if parsed.notna().any():
                date_min = parsed.min().date().isoformat()
                date_max = parsed.max().date().isoformat()
        records.append(
            {
                "Source File": table.source_file,
                "Source Table": table.source_table,
                "Rows": len(table.data),
                "Columns": len(table.data.columns),
                "Column Names": " | ".join(map(str, table.data.columns)),
                "Date Min": date_min,
                "Date Max": date_max,
                "Status": "Error" if table.error else "OK",
                "Error": table.error or "",
            }
        )
    return pd.DataFrame.from_records(records)


def load_mapping(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in payload.items()):
        raise ValueError("Mapping file must be a JSON object of source field to canonical field")
    return payload


def slugify(value: str) -> str:
    ascii_value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return ascii_value or "campaign"


def default_output_dir(campaign_name: str, base: Path | None = None) -> Path:
    root = base or Path("output")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return root / f"{slugify(campaign_name)}-{stamp}"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def dataframe_to_markdown(frame: pd.DataFrame, max_rows: int = 50) -> str:
    if frame.empty:
        return "_Not Available_"
    display = frame.head(max_rows).copy()
    headers = [str(column) for column in display.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in display.iterrows():
        values = [str(value).replace("|", "\\|").replace("\n", " ") if pd.notna(value) else "" for value in row]
        lines.append("| " + " | ".join(values) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only the first {max_rows} of {len(frame)} rows are shown._")
    return "\n".join(lines)
