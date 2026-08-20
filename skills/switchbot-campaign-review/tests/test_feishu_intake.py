from __future__ import annotations

import json
import shutil
import sys
import csv
from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_campaign_review as runner_module
from create_source_snapshot import create_snapshot
from feishu_common import FetchError, FetchResult, now_iso, paginated_cli, redact
from fetch_feishu_bitable import fetch_bitable
from fetch_feishu_sheet import fetch_sheet
from parse_feishu_url import extract_feishu_urls, parse_feishu_url
from run_campaign_review import run_campaign_review


def write_registry(path: Path, sources: list[dict], name: str = "Mock Campaign") -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "project": {
                    "name": name,
                    "market": "Japan",
                    "currency": "JPY",
                    "timezone": "Asia/Tokyo",
                },
                "sources": sources,
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    ("url", "source_type", "token"),
    [
        ("https://x.feishu.cn/base/bascn1?table=tbl1&view=vew1", "bitable", "bascn1"),
        ("https://x.feishu.cn/sheets/sht1?sheet=abc", "sheet", "sht1"),
        ("https://x.feishu.cn/docx/dox1", "docx", "dox1"),
        ("https://x.feishu.cn/wiki/wik1", "wiki", "wik1"),
        ("https://x.feishu.cn/file/f1", "unknown", None),
    ],
)
def test_parse_feishu_url_types_and_query(
    url: str, source_type: str, token: str | None
) -> None:
    parsed = parse_feishu_url(url)
    assert parsed["source_type"] == source_type
    assert parsed["token"] == token
    assert parsed["original_url"] == url
    if source_type == "bitable":
        assert parsed["table_id"] == "tbl1"
        assert parsed["view_id"] == "vew1"
    if source_type == "sheet":
        assert parsed["sheet_id"] == "abc"


def test_extract_urls_deduplicates_and_keeps_unknown() -> None:
    text = (
        "A https://x.feishu.cn/base/b1?table=t1 "
        "again https://x.feishu.cn/base/b1?table=t1 "
        "and https://x.feishu.cn/slides/s1"
    )
    parsed = extract_feishu_urls(text)
    assert len(parsed) == 2
    assert {item["source_type"] for item in parsed} == {"bitable", "unknown"}


def test_pagination_exhausts_all_pages_serially() -> None:
    calls: list[list[str]] = []

    def mock_runner(args: list[str], cwd: Path | None) -> dict:
        calls.append(args)
        offset = int(args[args.index("--offset") + 1]) if "--offset" in args else 0
        if offset == 0:
            return {"ok": True, "data": {"items": [{"record_id": "1"}], "has_more": True}}
        return {"ok": True, "data": {"items": [{"record_id": "2"}], "has_more": False}}

    items, pages = paginated_cli(
        ["base", "+record-list", "--base-token", "b", "--table-id", "t"],
        mock_runner,
        page_size=1,
    )
    assert [item["record_id"] for item in items] == ["1", "2"]
    assert len(pages) == 2
    assert "--offset" not in calls[0]
    assert calls[1][calls[1].index("--offset") + 1] == "1"


def test_bitable_empty_table_is_complete(tmp_path: Path) -> None:
    def mock_runner(args: list[str], cwd: Path | None) -> dict:
        command = args[1]
        if command == "+url-resolve":
            return {"ok": True, "data": {"base_token": "bas"}}
        if command == "+base-get":
            return {"ok": True, "data": {"name": "Empty Base"}}
        if command == "+table-list":
            return {
                "ok": True,
                "data": {"items": [{"table_id": "tbl", "name": "Empty"}], "has_more": False},
            }
        if command in {"+field-list", "+view-list", "+record-list"}:
            return {"ok": True, "data": {"items": [], "has_more": False}}
        raise AssertionError(args)

    results = fetch_bitable(
        {"id": "base", "name": "Base", "url": "https://x.feishu.cn/base/bas"},
        tmp_path,
        runner=mock_runner,
    )
    assert results[0].status == "Complete"
    assert results[0].row_count == 0


def test_bitable_missing_configured_table_fails(tmp_path: Path) -> None:
    def mock_runner(args: list[str], cwd: Path | None) -> dict:
        command = args[1]
        if command == "+url-resolve":
            return {"ok": True, "data": {"base_token": "bas"}}
        if command == "+base-get":
            return {"ok": True, "data": {"name": "Base"}}
        if command == "+table-list":
            return {
                "ok": True,
                "data": {"tables": [{"table_id": "other", "name": "Other"}], "has_more": False},
            }
        raise AssertionError(args)

    with pytest.raises(FetchError, match="Configured Base table not found"):
        fetch_bitable(
            {
                "id": "base",
                "name": "Base",
                "url": "https://x.feishu.cn/base/bas",
                "table_name": "required-table",
            },
            tmp_path,
            runner=mock_runner,
        )


def test_bitable_preserves_record_ids_and_complex_fields(tmp_path: Path) -> None:
    def mock_runner(args: list[str], cwd: Path | None) -> dict:
        command = args[1]
        payloads = {
            "+url-resolve": {"data": {"base_token": "bas"}},
            "+base-get": {"data": {"name": "Campaign Base"}},
            "+table-list": {
                "data": {"items": [{"table_id": "tbl", "name": "Delivery"}], "has_more": False}
            },
            "+field-list": {"data": {"items": [{"field_id": "f1"}], "has_more": False}},
            "+view-list": {"data": {"items": [{"view_id": "v1"}], "has_more": False}},
            "+record-list": {
                "data": {
                    "items": [
                        {
                            "record_id": "rec1",
                            "fields": {"Channel": "Google Ads", "Owner": [{"name": "A", "id": "u1"}]},
                        }
                    ],
                    "has_more": False,
                }
            },
        }
        return {"ok": True, **payloads[command]}

    result = fetch_bitable(
        {"id": "base", "name": "Base", "url": "https://x.feishu.cn/base/bas"},
        tmp_path,
        runner=mock_runner,
    )[0]
    normalized = tmp_path / result.normalized_file[0]
    text = normalized.read_text(encoding="utf-8-sig")
    assert "record_id" in text and "rec1" in text
    with normalized.open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["Owner"])[0]["id"] == "u1"
    assert result.metadata["field_count"] == 1


def test_sheet_reads_all_sheets_and_marks_hidden(tmp_path: Path) -> None:
    def mock_runner(args: list[str], cwd: Path | None) -> dict:
        command = args[1]
        if command == "+workbook-info":
            return {
                "ok": True,
                "data": {
                    "title": "Workbook",
                    "sheets": [
                        {"sheet_id": "s1", "title": "Current", "resource_type": "sheet"},
                        {"sheet_id": "s2", "title": "History", "resource_type": "sheet", "is_hidden": True},
                    ],
                },
            }
        if command == "+workbook-export":
            return {"ok": True, "data": {"status": "done"}}
        if command == "+table-get":
            return {
                "ok": True,
                "data": {
                    "sheets": [
                        {"sheet_id": "s1", "name": "Current", "columns": ["Channel"], "data": [["Google"]], "range": "A1:A2"},
                        {"sheet_id": "s2", "name": "History", "columns": ["Channel"], "data": [], "range": "A1:A1"},
                    ]
                },
            }
        raise AssertionError(args)

    results = fetch_sheet(
        {"id": "sheet", "name": "Sheet", "url": "https://x.feishu.cn/sheets/sht"},
        tmp_path,
        runner=mock_runner,
    )
    assert {item.object_name for item in results} == {"Current", "History"}
    history = next(item for item in results if item.object_name == "History")
    assert history.row_count == 0
    assert history.status == "Complete with Warnings"


def test_permission_failure_and_required_optional_statuses(tmp_path: Path) -> None:
    registry = write_registry(
        tmp_path / "sources.yaml",
        [
            {"id": "required", "name": "Required", "url": "https://x.feishu.cn/base/b1", "required": True},
            {"id": "optional", "name": "Optional", "url": "https://x.feishu.cn/docx/d1", "required": False},
        ],
    )

    def denied(args: list[str], cwd: Path | None) -> dict:
        raise FetchError("permission denied", status="Permission Required")

    snapshot = create_snapshot(registry, tmp_path / "snapshots", runner=denied, timestamp="2026-07-30_120000")
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "Partial"
    assert {entry["status"] for entry in manifest["sources"]} == {"Permission Required"}
    assert {entry["required"] for entry in manifest["sources"]} == {True, False}
    assert "Permission Required" in (snapshot / "source_integrity_report.md").read_text(encoding="utf-8")


def test_mid_api_failure_is_audited(tmp_path: Path) -> None:
    registry = write_registry(
        tmp_path / "sources.yaml",
        [{"id": "base", "name": "Base", "url": "https://x.feishu.cn/base/b1", "required": True}],
    )

    def failing(args: list[str], cwd: Path | None) -> dict:
        if args[1] == "+url-resolve":
            return {"ok": True, "data": {"base_token": "b1"}}
        raise FetchError("upstream timeout")

    snapshot = create_snapshot(registry, tmp_path / "snapshots", runner=failing, timestamp="2026-07-30_120001")
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sources"][0]["status"] == "Failed"
    assert manifest["sources"][0]["error"] == "upstream timeout"


def test_browser_fallback_is_unverified_and_manifested(tmp_path: Path) -> None:
    registry = write_registry(
        tmp_path / "sources.yaml",
        [{"id": "base", "name": "Base", "url": "https://x.feishu.cn/base/b1", "required": True}],
    )

    def denied(args: list[str], cwd: Path | None) -> dict:
        raise FetchError("login required", status="Permission Required")

    def browser(source: dict, snapshot: Path, error: FetchError) -> list[FetchResult]:
        export = snapshot / "normalized" / "base__browser.csv"
        export.write_text("Channel,Spend\nGoogle Ads,100\n", encoding="utf-8")
        return [
            FetchResult(
                source_id="base",
                source_name="Base",
                source_url=source["url"],
                source_type="bitable",
                retrieval_method="browser-export",
                retrieval_time=now_iso(),
                status="Unverified",
                warning=["Completeness unknown"],
                normalized_file=["normalized/base__browser.csv"],
            )
        ]

    snapshot = create_snapshot(
        registry,
        tmp_path / "snapshots",
        runner=denied,
        browser_fallback=True,
        browser_adapter=browser,
        timestamp="2026-07-30_120002",
    )
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sources"][0]["retrieval_method"] == "browser-export"
    assert manifest["sources"][0]["status"] == "Unverified"


def test_wiki_doc_route_exports_structured_and_markdown_snapshots(tmp_path: Path) -> None:
    registry = write_registry(
        tmp_path / "sources.yaml",
        [{"id": "wiki", "name": "Wiki", "url": "https://x.feishu.cn/wiki/w1", "required": True}],
    )

    def mock_runner(args: list[str], cwd: Path | None) -> dict:
        if args[:2] == ["wiki", "+node-get"]:
            return {
                "ok": True,
                "data": {"node": {"obj_type": "docx", "obj_token": "d1"}},
            }
        if args[:2] == ["docs", "+fetch"]:
            doc_format = args[args.index("--doc-format") + 1]
            content = (
                "<title>Campaign Brief</title><h1>Objective</h1><p>Launch</p>"
                if doc_format == "xml"
                else "# Campaign Brief\n\n| Channel | Spend |\n|---|---:|\n| Google Ads | 100 |\n"
            )
            return {
                "ok": True,
                "data": {
                    "document": {
                        "title": "Campaign Brief",
                        "revision_id": 3,
                        "content": content,
                    }
                },
            }
        raise AssertionError(args)

    snapshot = create_snapshot(
        registry,
        tmp_path / "snapshots",
        runner=mock_runner,
        timestamp="2026-07-30_120009",
    )
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["sources"][0]
    assert entry["source_type"] == "wiki"
    assert entry["metadata"]["resolved_object_type"] == "docx"
    assert entry["normalized_sha256"]
    assert (snapshot / entry["normalized_file"][0]).read_text(encoding="utf-8").startswith(
        "# Campaign Brief"
    )


def test_secret_redaction_is_recursive() -> None:
    payload = {
        "access_token": "abc",
        "nested": {"Authorization": "Bearer secret-token"},
        "message": "app_secret=do-not-log",
        "cookie_text": "Cookie: cookie-secret; other=value",
        "session_text": "session=secret-session",
        "session_token_text": "session_token=secret-session-token",
        "basic_text": "Authorization: Basic secret-basic",
    }
    cleaned = redact(payload)
    serialized = json.dumps(cleaned)
    assert "abc" not in serialized
    assert "secret-token" not in serialized
    assert "do-not-log" not in serialized
    assert "cookie-secret" not in serialized
    assert "secret-session" not in serialized
    assert "secret-session-token" not in serialized
    assert "secret-basic" not in serialized
    assert serialized.count("[REDACTED]") == 7


def test_analyze_only_never_fetches_and_generates_snapshot_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    for name in ("sample_campaign_data.csv", "sample_previous_campaign_data.csv"):
        shutil.copy2(SKILL_DIR / "examples" / name, input_dir / name)
    registry = write_registry(
        tmp_path / "sources.yaml",
        [
            {"id": name, "name": name, "url": str(input_dir / name), "source_type": "file", "required": True}
            for name in ("sample_campaign_data.csv", "sample_previous_campaign_data.csv")
        ],
        name="Snapshot Campaign",
    )
    snapshot = create_snapshot(registry, tmp_path / "snapshots", timestamp="2026-07-30_120003")

    def forbidden_fetch(*args, **kwargs):
        raise AssertionError("analyze-only must not fetch")

    monkeypatch.setattr(runner_module, "create_snapshot", forbidden_fetch)
    output = run_campaign_review(
        sources=registry,
        output_dir=tmp_path / "output",
        analyze_only=True,
        snapshot=snapshot,
    )
    assert (output / "source_integrity_report.md").is_file()
    report = (output / "full_analysis.md").read_text(encoding="utf-8")
    assert "Data Snapshot" in report
    assert "2026-07-30_120003" in report


def test_snapshot_registry_mismatch_blocks_analysis(tmp_path: Path) -> None:
    data = tmp_path / "data.csv"
    data.write_text("Channel,Spend\nGoogle Ads,1\n", encoding="utf-8")
    registry = write_registry(
        tmp_path / "sources.yaml",
        [{"id": "data", "url": str(data), "source_type": "file", "required": True}],
    )
    snapshot = create_snapshot(registry, tmp_path / "snapshots", timestamp="2026-07-30_120004")
    write_registry(
        registry,
        [{"id": "changed", "url": str(data), "source_type": "file", "required": True}],
    )
    with pytest.raises(ValueError, match="mismatch"):
        run_campaign_review(
            sources=registry,
            output_dir=tmp_path / "output",
            analyze_only=True,
            snapshot=snapshot,
        )


def test_snapshot_checksum_mismatch_blocks_analysis(tmp_path: Path) -> None:
    data = tmp_path / "data.csv"
    data.write_text("Channel,Spend\nGoogle Ads,1\n", encoding="utf-8")
    registry = write_registry(
        tmp_path / "sources.yaml",
        [{"id": "data", "url": str(data), "source_type": "file", "required": True}],
    )
    snapshot = create_snapshot(registry, tmp_path / "snapshots", timestamp="2026-07-30_120005")
    normalized = next((snapshot / "normalized").glob("*.csv"))
    normalized.write_text(normalized.read_text(encoding="utf-8") + "Meta Ads,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        run_campaign_review(
            sources=registry,
            output_dir=tmp_path / "output",
            analyze_only=True,
            snapshot=snapshot,
        )


def test_untracked_normalized_file_blocks_analysis(tmp_path: Path) -> None:
    data = tmp_path / "data.csv"
    data.write_text("Channel,Spend\nGoogle Ads,1\n", encoding="utf-8")
    registry = write_registry(
        tmp_path / "sources.yaml",
        [{"id": "data", "url": str(data), "source_type": "file", "required": True}],
    )
    snapshot = create_snapshot(registry, tmp_path / "snapshots", timestamp="2026-07-30_120010")
    (snapshot / "normalized" / "untracked.csv").write_text(
        "Channel,Spend\nInjected,999\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="file set mismatch"):
        run_campaign_review(
            sources=registry,
            output_dir=tmp_path / "output",
            analyze_only=True,
            snapshot=snapshot,
        )


def test_same_registry_creates_fresh_snapshot_by_default(tmp_path: Path) -> None:
    data = tmp_path / "data.csv"
    data.write_text("Channel,Spend\nGoogle Ads,1\n", encoding="utf-8")
    registry = write_registry(
        tmp_path / "sources.yaml",
        [{"id": "data", "url": str(data), "source_type": "file", "required": True}],
    )
    first = create_snapshot(registry, tmp_path / "snapshots", timestamp="2026-07-30_120006")
    second = create_snapshot(registry, tmp_path / "snapshots", timestamp="2026-07-30_120007")
    assert first != second
    assert first.is_dir() and second.is_dir()


def test_source_filter_marks_omitted_required_source_partial_and_lowers_confidence(
    tmp_path: Path,
) -> None:
    current = tmp_path / "current.csv"
    omitted = tmp_path / "omitted.csv"
    shutil.copy2(SKILL_DIR / "examples" / "sample_campaign_data.csv", current)
    omitted.write_text("Channel,Spend\nMeta Ads,100\n", encoding="utf-8")
    registry = write_registry(
        tmp_path / "sources.yaml",
        [
            {"id": "current", "url": str(current), "source_type": "file", "required": True},
            {"id": "omitted", "url": str(omitted), "source_type": "file", "required": True},
        ],
        name="Prime Day 2026",
    )
    snapshot = create_snapshot(
        registry,
        tmp_path / "snapshots",
        source_ids={"current"},
        timestamp="2026-07-30_120008",
    )
    snapshot_manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    omitted_entry = next(
        entry for entry in snapshot_manifest["sources"] if entry["source_id"] == "omitted"
    )
    assert snapshot_manifest["status"] == "Partial"
    assert omitted_entry["status"] == "Partial"
    output = run_campaign_review(
        sources=registry,
        output_dir=tmp_path / "output",
        analyze_only=True,
        snapshot=snapshot,
    )
    run_manifest = json.loads(
        (output / "_intermediate" / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert run_manifest["status"] == "partial"
    assert run_manifest["source_snapshot"]["required_source_gaps"] == ["omitted"]
    evaluation = __import__("pandas").read_csv(output / "channel_evaluation.csv")
    assert evaluation["Confidence"].eq("Low").all()
    assert evaluation["Decision"].eq("Insufficient Data").all()
    budget = __import__("pandas").read_csv(
        output / "_intermediate" / "budget_recommendations.csv"
    )
    assert budget["Confidence"].eq("Low").all()
    assert budget["Direction"].eq("Insufficient Data").all()
    assert budget["Recommended Budget Index"].isna().all()
    actions = __import__("pandas").read_csv(output / "action_plan.csv")
    assert actions["Confidence"].eq("Low").all()
    assert actions["Action"].str.contains("补齐并重新抓取必需数据源").any()
    assert not actions["Action"].str.contains("增加 KOL").any()
