from __future__ import annotations

from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_UPGRADE_TASK_PLAN_V1"

IMPORT_BLOCK = '''from meina_task_plans import detect_task_plan, get_task_plan, validate_task_plan

# MEINA_UPGRADE_TASK_PLAN_V1
_original_route_command = command_router.route_command


def _route_command_with_task_plan(text, frame):
    plan_name = detect_task_plan(text)
    if plan_name and validate_task_plan(plan_name):
        try:
            confidence = float(frame.get("confidence", 0))
        except (AttributeError, TypeError, ValueError):
            confidence = 0.0
        if confidence >= command_router.MIN_CONFIDENCE:
            return {
                "kind": "task_plan",
                "target": plan_name,
                "query": None,
                "confidence": confidence,
            }
    return _original_route_command(text, frame)


command_router.route_command = _route_command_with_task_plan
'''

EXEC_BLOCK = '''# MEINA_UPGRADE_TASK_PLAN_V1_EXEC


def execute_task_plan(route):
    """固定定義されたタスクだけを順番に実行する。"""
    plan_name = route.get("target")
    if not plan_name or not validate_task_plan(plan_name):
        print("⚠️ 不正なタスク計画のため実行しません")
        return False

    plan = get_task_plan(plan_name)
    print("🧩 タスク計画:", plan_name)

    for index, step in enumerate(plan, 1):
        print(f"  [{index}/{len(plan)}] {step['label']}")
        step_route = {
            "kind": step["kind"],
            "target": step["target"],
            "query": step.get("query"),
            "confidence": route.get("confidence", 1.0),
        }
        if not _execute_routed_command_base(step_route):
            print("❌ タスク計画を中断しました:", step["label"])
            speak("配信準備を中断しました")
            return True

    print("✅ タスク計画完了:", plan_name)
    speak("配信準備が完了しました")
    return True


'''


def main() -> None:
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")

    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Meina task plan upgrade: already applied")
        return

    backup = AGENT.with_name("meina_agent.py.backup_before_task_plan")
    if not backup.exists():
        shutil.copy2(AGENT, backup)

    anchor = "import command_router\n"
    if anchor not in text:
        raise SystemExit("command_router import が見つかりません")
    text = text.replace(anchor, anchor + IMPORT_BLOCK + "\n", 1)

    old_name = "def execute_routed_command(route):"
    if old_name not in text:
        raise SystemExit("execute_routed_command が見つかりません")
    text = text.replace(old_name, "def _execute_routed_command_base(route):", 1)

    action_anchor = "def execute_action(frame):"
    if action_anchor not in text:
        raise SystemExit("execute_action が見つかりません")
    wrapper = "def execute_routed_command(route):\n    if route.get(\"kind\") == \"task_plan\":\n        return execute_task_plan(route)\n    return _execute_routed_command_base(route)\n\n\n" + EXEC_BLOCK
    text = text.replace(action_anchor, wrapper + action_anchor, 1)

    AGENT.write_text(text, encoding="utf-8")
    print("Meina task plan upgrade: applied")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
