"""Twitch自動切り抜きの本番入口がV2重複防止実装を使うことを確認する。"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    source = (ROOT / "twitch_auto_clip.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="twitch_auto_clip.py")

    imports_v2 = False
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "twitch_auto_clip_v2":
            imports_v2 = any(alias.name == "process_new_vod" for alias in node.names)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                calls.append(func.attr)

    assert imports_v2, "twitch_auto_clip.py must import process_new_vod"
    assert "process_new_vod" in calls, "twitch_auto_clip.py must call process_new_vod"
    assert "create_ai_clips" not in calls, "legacy V1 clipping path must not remain"
    assert "process_latest_vod" not in calls, "legacy V1 VOD path must not remain"

    v2 = (ROOT / "twitch_auto_clip_v2.py").read_text(encoding="utf-8")
    assert "last_vod_id" in v2
    assert "return None" in v2

    print("Twitch auto-clip V2 wiring self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
