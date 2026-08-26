from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _frontmatter(text: str) -> dict:
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_campaign_entry_contract():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    ui = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    reference = (ROOT / "references" / "campaign-lifecycle.md").read_text(encoding="utf-8")

    meta = _frontmatter(skill)
    assert meta["name"] == "switchbot-japan-campaign"
    assert "营销渠道素材需求汇总" in skill
    assert "促销项目目标和数据复盘" in skill
    assert "NEED_CONFIRMATION" in skill
    assert "不得自动创建或上传 Bitly" in skill
    assert "Amazon Attribution" in skill
    assert ui["policy"]["allow_implicit_invocation"] is True
    assert ui["interface"]["display_name"] == "日本营销活动策划与复盘"

    for legacy in ("gtm-thinking-framework", "jp-traffic-link-governance", "switchbot-campaign-review"):
        assert legacy in reference


def test_campaign_historical_and_write_gates():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "历史项目只能继承结构、规则和可比数据" in skill
    assert "历史格式未验证" in skill
    assert "不得自动修改正式飞书表" in skill
