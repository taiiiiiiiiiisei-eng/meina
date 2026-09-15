from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = {
    "twitch_auto_clip_v2.py": ["process_new_vod", "main"],
    "twitch_ffmpeg_env.py": ["find_executable"],
    "twitch_clip_pipeline.py": ["load_config", "get_latest_vod", "download_vod", "load_state", "save_state"],
    "twitch_ai_clipper.py": ["create_ai_clips", "_select_non_overlapping"],
    "twitch_video_editor.py": ["edit_clip", "edit_generated_clip"],
}


def main() -> None:
    errors: list[str] = []
    for filename, functions in REQUIRED.items():
        path = ROOT / filename
        if not path.exists():
            errors.append(f"missing: {filename}")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=filename)
        except SyntaxError as exc:
            errors.append(f"syntax: {filename}: {exc}")
            continue
        names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for function in functions:
            if function not in names:
                errors.append(f"missing function: {filename}:{function}")

    if errors:
        print("❌ Twitch self-test V2 failed")
        for error in errors:
            print(" -", error)
        raise SystemExit(1)

    print("✅ Twitch self-test V2 OK")


if __name__ == "__main__":
    main()
