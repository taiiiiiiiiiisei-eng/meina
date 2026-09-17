from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
ROUTER = ROOT / "command_router.py"

AGENT_MARKER = "# MEINA_UPGRADE_TASK_PLAN_LOCAL_V1"
ROUTER_MARKER = "# MEINA_TASK_PLAN_ROUTER_LOCAL_V1"


def main() -> None:
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")
    if not ROUTER.exists():
        raise SystemExit("command_router.py が見つかりません")

    backup = AGENT.with_name("meina_agent.py.backup_before_task_plan_local")
    if not backup.exists():
        shutil.copy2(AGENT, backup)
        print(f"Backup created: {backup}")

    # command_router: 固定・許可済みの「配信準備」は
    # brain_core の自然言語 confidence に依存させない。
    router_text = ROUTER.read_text(encoding="utf-8")
    if ROUTER_MARKER not in router_text:
        marker = '    if not text or _confidence(frame) < MIN_CONFIDENCE:\n        return None\n'
        if marker not in router_text:
            raise SystemExit("command_router.py の安全チェック位置を特定できません")

        replacement = '''    # MEINA_TASK_PLAN_ROUTER_LOCAL_V1
    # 「配信準備」は固定・許可済みタスクなので
    # brain_coreの自然言語confidenceには依存しない。
    compact_for_task = _compact(text)
    if "配信準備" in compact_for_task:
        return {
            "kind": "task_plan",
            "target": "stream_prepare",
            "query": None,
            "confidence": 1.0,
        }

''' + marker
        router_text = router_text.replace(marker, replacement, 1)
        ROUTER.write_text(router_text, encoding="utf-8")
        print("command_router.py: task plan routing applied")
    else:
        print("command_router.py: already patched")

    # meina_agent: task_plan を固定手順として安全に実行する。
    agent_text = AGENT.read_text(encoding="utf-8")
    if AGENT_MARKER not in agent_text:
        import_anchor = "import command_router\n"
        if import_anchor not in agent_text:
            raise SystemExit("command_router import が見つかりません")

        import_block = '''import command_router
from meina_task_plans import get_task_plan, validate_task_plan

# MEINA_UPGRADE_TASK_PLAN_LOCAL_V1
'''
        agent_text = agent_text.replace(import_anchor, import_block, 1)

        function_anchor = 'def execute_routed_command(route):\n'
        if function_anchor not in agent_text:
            raise SystemExit("execute_routed_command が見つかりません")
        agent_text = agent_text.replace(
            function_anchor,
            'def _execute_routed_command_base(route):\n',
            1,
        )

        insert_anchor = 'def execute_action(frame):\n'
        if insert_anchor not in agent_text:
            raise SystemExit("execute_action が見つかりません")

        task_block = '''# MEINA_UPGRADE_TASK_PLAN_LOCAL_V1_EXEC

def execute_task_plan(route):
    """安全な固定タスクだけを順番に実行する。"""
    plan_name = route.get("target")
    if not plan_name or not validate_task_plan(plan_name):
        print("⚠️ 不正なタスク計画のため実行しません")
        return False

    plan = get_task_plan(plan_name)
    print("")
    print("🧩 固定タスク計画:", plan_name)

    for index, step in enumerate(plan, 1):
        print(f"  [{index}/{len(plan)}] {step['label']}")
        step_route = {
            "kind": step["kind"],
            "target": step["target"],
            "query": step.get("query"),
            "confidence": 1.0,
        }
        if not _execute_routed_command_base(step_route):
            print("❌ タスク計画を中断:", step["label"])
            speak("配信準備を中断しました")
            return True

    print("✅ 配信準備完了")
    speak("配信準備が完了しました")
    return True


def execute_routed_command(route):
    if route.get("kind") == "task_plan":
        return execute_task_plan(route)
    return _execute_routed_command_base(route)


'''
        agent_text = agent_text.replace(insert_anchor, task_block + insert_anchor, 1)
        AGENT.write_text(agent_text, encoding="utf-8")
        print("meina_agent.py: task plan integration applied")
    else:
        print("meina_agent.py: already patched")

    print("")
    print("========================================")
    print("配信準備タスクプラン導入完了")
    print("========================================")


if __name__ == "__main__":
    main()
