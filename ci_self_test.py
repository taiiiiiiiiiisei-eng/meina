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
    "meina2/tools.py": ["open_browser", "google_search", "youtube_search"],
    "meina_brain/brain_core.py": ["process_command"],
    "twitch_clip_pipeline.py": ["process_latest_vod", "transcribe_vod"],
    "twitch_ai_clipper.py": ["create_ai_clips"],
    "twitch_video_editor.py": ["edit_generated_clip"],
    "meina_twitch.py": ["run_twitch_clip_command"],
    "meina_twitch_voice.py": ["handle_voice_command"],
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

    print("CI static self-test passed")


if __name__ == "__main__":
    main()
