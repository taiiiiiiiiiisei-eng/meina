"""Current task-plan integration self-test."""
from pathlib import Path

from meina_task_plans import get_task_plan, validate_task_plan, detect_task_plan

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
UPGRADE = ROOT / "upgrade_meina_task_plan.py"


def check_plan(name, expected_game):
    plan = get_task_plan(name)
    assert validate_task_plan(name), name
    assert plan is not None and len(plan) == 3
    assert plan[0]["target"] == "OBS"
    assert plan[1]["target"] == "Discord"
    assert plan[2]["target"] == expected_game


def main() -> int:
    assert AGENT.exists()
    assert UPGRADE.exists()
    source = UPGRADE.read_text(encoding="utf-8")
    assert "execute_task_plan" in source
    assert "validate_task_plan" in source
    assert detect_task_plan("配信準備して") == "stream_prepare_valorant"
    assert detect_task_plan("VALORANTの配信準備して") == "stream_prepare_valorant"
    assert detect_task_plan("Apexの配信準備して") == "stream_prepare_apex"
    check_plan("stream_prepare_valorant", "VALORANT")
    check_plan("stream_prepare_apex", "Apex")
    assert get_task_plan("stream_prepare") is None

    # 不正な対象やkindは許可しない。
    from meina_task_plans import TASK_PLANS
    TASK_PLANS["__invalid_target__"] = (
        {"kind": "app_open", "target": "powershell", "label": "不正な起動"},
    )
    TASK_PLANS["__invalid_kind__"] = (
        {"kind": "shell", "target": "OBS", "label": "不正な処理"},
    )
    TASK_PLANS["__invalid_label__"] = (
        {"kind": "app_open", "target": "OBS", "label": ""},
    )
    try:
        assert not validate_task_plan("__invalid_target__")
        assert not validate_task_plan("__invalid_kind__")
        assert not validate_task_plan("__invalid_label__")
    finally:
        TASK_PLANS.pop("__invalid_target__", None)
        TASK_PLANS.pop("__invalid_kind__", None)
        TASK_PLANS.pop("__invalid_label__", None)
    print("Task plan integration self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
