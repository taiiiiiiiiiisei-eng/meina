from meina_task_plans import detect_task_plan, get_task_plan, validate_task_plan


def main() -> int:
    assert detect_task_plan("配信準備して") == "stream_prepare"
    assert detect_task_plan("メモ帳を開いて") is None
    plan = get_task_plan("stream_prepare")
    assert plan and len(plan) == 3
    assert validate_task_plan("stream_prepare")
    assert not validate_task_plan("unknown")
    print("Task plan self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
