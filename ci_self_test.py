"""CI用の依存関係なし静的セルフテスト。"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = {
    "meina_agent.py": ["process_command"],
    "command_router.py": ["route_command"],
    "meina_pc_status.py": ["get_pc_status", "format_pc_status"],
    "meina_task_plans.py": ["detect_task_plan", "get_task_plan", "validate_task_plan"],
    "upgrade_meina_task_plan.py": ["main"],
    "meina2/tools.py": ["open_browser", "google_search", "youtube_search"],
    "meina_brain/brain_core.py": ["extract_action_frame", "infer_intent"],
    "twitch_clip_pipeline.py": ["process_latest_vod", "transcribe_vod"],
    "twitch_ai_clipper.py": ["create_ai_clips"],
    "twitch_video_editor.py": ["edit_generated_clip"],
    "meina_twitch.py": ["run_twitch_clip_command"],
    "meina_twitch_voice.py": ["handle_voice_command"],
    "meina_reminders.py": ["add_reminder", "list_reminders", "today_reminders", "tomorrow_reminders", "upcoming_reminders"],
    "meina_reminder_parser.py": ["parse_reminder_command"],
}


def public_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def main() -> None:
    for relative, required in REQUIRED_FILES.items():
        path = ROOT / relative
        assert path.exists(), f"missing: {relative}"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        names = public_names(tree)
        for name in required:
            assert name in names, f"{relative}: missing {name}"
        print(f"OK: {relative}")

    router = (ROOT / "command_router.py").read_text(encoding="utf-8")
    task_upgrade = (ROOT / "upgrade_meina_task_plan.py").read_text(encoding="utf-8")
    task_plan = (ROOT / "meina_task_plans.py").read_text(encoding="utf-8")
    launcher = (ROOT / "start_meina.bat").read_text(encoding="utf-8")

    assert '"kind": "task_plan"' in router
    assert '"reminder_upcoming"' in router
    assert '"予定を追加"' in router
    assert '"kind": "weather"' in router
    assert '"query": mode' in router
    assert "stream_prepare" in task_plan
    assert "配信準備" in task_plan
    assert '"app_open"' in task_plan
    assert '"web_open"' in task_plan
    assert "MEINA_UPGRADE_TASK_PLAN_V1" in task_upgrade
    assert "execute_task_plan" in task_upgrade
    assert "upgrade_meina_reminders_v7.py" in launcher
    assert "MEINA_REMINDER_COMMANDS_V7" in (ROOT / "upgrade_meina_reminders_v7.py").read_text(encoding="utf-8")

    print("CI static self-test passed")


if __name__ == "__main__":
    main()
