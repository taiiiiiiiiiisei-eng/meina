from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "twitch_clip_pipeline.py",
    "twitch_ai_clipper.py",
    "twitch_auto_clip.py",
    "meina_twitch.py",
    "meina_twitch_voice.py",
    "twitch_clip_runner.py",
    "upgrade_meina_twitch.py",
]

REQUIRED_PIPELINE_NAMES = {
    "twitch_app_token",
    "get_user_id",
    "get_latest_vod",
    "download_vod",
    "transcribe_vod",
    "_duration_seconds",
    "make_clip",
    "process_latest_vod",
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
            if name == "twitch_clip_pipeline.py":
                found = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                missing = REQUIRED_PIPELINE_NAMES - found
                if missing:
                    print(f"FAIL pipeline functions: {sorted(missing)}")
                    failed = True
        except Exception as exc:
            print(f"FAIL syntax: {name}: {exc}")
            failed = True

    print("Twitch self test: FAIL" if failed else "Twitch self test: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
