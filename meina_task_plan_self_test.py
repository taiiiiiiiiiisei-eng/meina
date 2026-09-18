"""固定タスク計画と安全ルーターの依存関係なしセルフテスト。"""

from __future__ import annotations

from meina_task_plans import detect_task_plan, get_task_plan, validate_task_plan
from command_router import route_command


def main() -> int:
    assert detect_task_plan("配信準備して") == "stream_prepare_valorant"
    assert detect_task_plan("メモ帳を開いて") is None

    plan = get_task_plan("stream_prepare_valorant")
    assert plan and len(plan) == 3
    assert validate_task_plan("stream_prepare_valorant")
    assert not validate_task_plan("unknown")

    route = route_command(
        "配信準備して",
        {"confidence": 0.25},
    )
    assert route == {
        "kind": "task_plan",
        "target": "stream_prepare_valorant",
        "query": None,
        "confidence": 1.0,
    }

    print("Task plan self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
