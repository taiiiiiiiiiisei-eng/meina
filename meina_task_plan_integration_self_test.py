from pathlib import Path

from meina_task_plans import get_task_plan, validate_task_plan

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
UPGRADE = ROOT / "upgrade_meina_task_plan.py"


def main() -> int:
    assert AGENT.exists()
    assert UPGRADE.exists()
    source = UPGRADE.read_text(encoding="utf-8")
    assert "MEINA_UPGRADE_TASK_PLAN_V1" in source
    assert "_route_command_with_task_plan" in source
    assert "execute_task_plan" in source
    plan = get_task_plan("stream_prepare")
    assert validate_task_plan("stream_prepare")
    assert plan[0]["target"] == "OBS"
    assert plan[1]["target"] == "Discord"
    assert plan[2]["target"] == "youtube"
    print("Task plan integration self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
