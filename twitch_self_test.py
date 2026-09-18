from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "twitch_clip_pipeline.py",
    "twitch_ai_clipper.py",
    "twitch_auto_clip.py",
    "twitch_auto_clip_v2.py",
    "twitch_auto_clip_self_test.py",
    "twitch_ffmpeg_env.py",
    "twitch_video_editor.py",
    "meina_twitch.py",
    "meina_twitch_intent.py",
    "meina_twitch_voice.py",
    "twitch_clip_runner.py",
    "upgrade_meina_twitch.py",
]

REQUIRED_NAMES = {
    "twitch_clip_pipeline.py": {
        "twitch_app_token", "get_user_id", "get_latest_vod", "download_vod",
        "transcribe_vod", "_duration_seconds", "make_clip", "process_latest_vod",
    },
    "twitch_auto_clip_v2.py": {"process_new_vod", "main"},
    "twitch_ffmpeg_env.py": {"find_executable"},
    "twitch_ai_clipper.py": {"create_ai_clips", "_select_non_overlapping"},
    "twitch_video_editor.py": {"edit_clip", "edit_generated_clip"},
    "meina_twitch.py": {"_requested_day", "clip_latest_twitch_stream", "run_twitch_clip_command"},
    "meina_twitch_intent.py": {"is_twitch_clip_request", "requested_day"},
    "meina_twitch_voice.py": {"handle_voice_command"},
    "twitch_clip_runner.py": {"main"},
    "upgrade_meina_twitch.py": {"main"},
}


def main() -> int:
    failed = False
    for name in FILES:
        path = ROOT / name
        if not path.exists():
            print(f"FAIL missing: {name}")
            failed = True
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=name)
            print(f"OK syntax: {name}")
            required = REQUIRED_NAMES.get(name, set())
            found = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            missing = required - found
            if missing:
                print(f"FAIL functions: {name}: {sorted(missing)}")
                failed = True
        except Exception as exc:
            print(f"FAIL syntax: {name}: {exc}")
            failed = True

    print("Twitch self test: FAIL" if failed else "Twitch self test: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
