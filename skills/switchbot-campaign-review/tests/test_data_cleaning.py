from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from clean_marketing_data import (
    apply_campaign_identity,
    clean_tables,
    normalize_percent_series,
)
from common import (
    SourceTable,
    discover_source_files,
    map_columns,
    parse_number,
    scan_input_directory,
)


def test_field_aliases_map_to_canonical_names() -> None:
    frame = pd.DataFrame({"Ad Spend": [100], "表示回数": [1000], "クリック": [50], "売上": [300]})
    normalized, mapped, unmapped = map_columns(frame)
    assert {"spend", "impressions", "clicks", "revenue"}.issubset(normalized.columns)
    assert not unmapped
    assert mapped["Ad Spend"] == "spend"


def test_exact_duplicates_and_summary_rows_are_excluded() -> None:
    frame = pd.DataFrame(
        [
            {"Year": 2026, "Media": "Google Ads", "Ad Spend": 100, "Impression": 1000, "Click": 100, "CTR": "10%"},
            {"Year": 2026, "Media": "Google Ads", "Ad Spend": 100, "Impression": 1000, "Click": 100, "CTR": "10%"},
            {"Year": 2026, "Media": "Total", "Ad Spend": 200, "Impression": 2000, "Click": 200, "CTR": "10%"},
        ]
    )
    cleaned, issues, _, _, excluded = clean_tables([SourceTable("sample.csv", "sample", frame)])
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["ctr"] == pytest.approx(0.1)
    assert len(excluded) == 2
    assert set(excluded["_exclusion_reason"]) == {"Exact duplicate", "Summary or total row"}
    assert {"Exact duplicate rows", "Summary rows mixed with detail"}.issubset(set(issues["Issue Type"]))


def test_mixed_percentage_scale_is_flagged() -> None:
    issues: list[dict[str, object]] = []
    result = normalize_percent_series(
        pd.Series(["2.5%", 0.04, 5]),
        "ctr",
        "sample.csv",
        "sample",
        issues,
    )
    assert result.iloc[0] == pytest.approx(0.025)
    assert result.iloc[1] == pytest.approx(0.04)
    assert result.iloc[2] == pytest.approx(5)
    assert any(row["Issue Type"] == "Mixed percentage scale" for row in issues)


def test_fullwidth_percent_and_currency_formats_are_parsed() -> None:
    issues: list[dict[str, object]] = []
    rates = normalize_percent_series(
        pd.Series(["１２．５％", "0.25"]),
        "ctr",
        "sample.csv",
        "sample",
        issues,
    )
    assert rates.iloc[0] == pytest.approx(0.125)
    assert rates.iloc[1] == pytest.approx(0.25)
    assert parse_number("JPY 1,234") == 1234
    assert parse_number("（￥2,500）") == -2500


def test_arrow_string_null_does_not_break_percent_normalization() -> None:
    issues: list[dict[str, object]] = []
    rates = normalize_percent_series(
        pd.Series(["2.5%", None], dtype="string[pyarrow]"),
        "ctr",
        "sample.csv",
        "sample",
        issues,
    )
    assert rates.iloc[0] == pytest.approx(0.025)
    assert pd.isna(rates.iloc[1])


def test_formula_error_is_detected_before_numeric_coercion() -> None:
    frame = pd.DataFrame(
        [
            {
                "Year": 2032,
                "Media": "Google Ads",
                "Ad Spend": "#DIV/0!",
                "Impression": 1000,
                "Click": 100,
            }
        ]
    )
    cleaned, issues, _, _, _ = clean_tables(
        [SourceTable("formula.csv", "formula", frame)]
    )
    assert pd.isna(cleaned.iloc[0]["spend"])
    assert "Formula error strings" in set(issues["Issue Type"])
    assert "Invalid numeric values" in set(issues["Issue Type"])


def test_scanner_reads_every_file_and_every_excel_sheet(tmp_path: Path) -> None:
    input_dir = tmp_path / "campaign-data"
    input_dir.mkdir()
    workbook_path = input_dir / "multi_sheet.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame({"Year": [2031], "Media": ["Google Ads"]}).to_excel(
            writer, sheet_name="Current", index=False
        )
        pd.DataFrame({"Year": [2030], "Media": ["YouTube Ads"]}).to_excel(
            writer, sheet_name="Previous", index=False
        )
    (input_dir / "extra.csv").write_text("Year,Media\n2032,EDM\n", encoding="utf-8")

    tables = scan_input_directory(input_dir)
    assert {(Path(table.source_file).name, table.source_table) for table in tables} == {
        ("multi_sheet.xlsx", "Current"),
        ("multi_sheet.xlsx", "Previous"),
        ("extra.csv", "extra"),
    }


def test_input_root_named_output_is_not_silently_skipped(tmp_path: Path) -> None:
    input_dir = tmp_path / "output-campaign-source"
    input_dir.mkdir()
    source = input_dir / "campaign.csv"
    source.write_text("Year,Media\n2032,Google Ads\n", encoding="utf-8")
    nested = input_dir / "output-data"
    nested.mkdir()
    nested_source = nested / "historical.tsv"
    nested_source.write_text("Year\tMedia\n2031\tEDM\n", encoding="utf-8")
    assert discover_source_files(input_dir) == [source, nested_source]


def test_report_campaign_identity_conflict_is_critical_and_auditable() -> None:
    frame = pd.DataFrame(
        {
            "campaign": ["Prime Day 2031", "Prime Day 2032"],
            "period": ["2031", "2032"],
        }
    )
    issues: list[dict[str, object]] = []
    checked, metadata = apply_campaign_identity(
        frame, issues, "Autumn Smart Home Launch"
    )
    assert metadata["status"] == "conflict"
    assert checked["campaign_identity_status"].eq("conflict").all()
    assert issues[0]["Severity"] == "Critical"


def test_campaign_identity_ignores_year_for_same_campaign_family() -> None:
    frame = pd.DataFrame({"campaign": ["Prime Day 2031", "Prime Day 2032"]})
    issues: list[dict[str, object]] = []
    _, metadata = apply_campaign_identity(frame, issues, "Prime Day")
    assert metadata["status"] == "verified"
    assert not issues
