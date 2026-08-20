from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from collect_api_channels import is_natural_comment


def test_comment_eligibility_separates_opinion_and_promotion() -> None:
    assert is_natural_comment("画質は少し暗いけど部屋に飾ると素敵")[0] == "Natural VOC"
    assert is_natural_comment("#PR Amazonセール中 amazon.co.jp/dp/example")[0] == "Context Only"
    assert is_natural_comment("見ました")[0] == "Unverified"
