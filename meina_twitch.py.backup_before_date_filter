from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from twitch_ai_clipper import create_ai_clips
from twitch_clip_pipeline import process_latest_vod


def is_twitch_clip_request(text: str) -> bool:
    compact = re.sub(r"\s+", "", text).lower()
    return (
        ("切り抜" in compact or "ハイライト" in compact)
        and ("配信" in compact or "twitch" in compact or "昨日" in compact or "今日" in compact or "最近" in compact)
    )


def clip_latest_twitch_stream(max_clips: int = 3) -> list[Path]:
    vod = process_latest_vod(download_only=True)
    if vod is None:
        raise RuntimeError("TwitchのVODを取得できませんでした")
    return create_ai_clips(vod, max_clips=max_clips)


def run_twitch_clip_command(text: str, max_clips: int = 3) -> dict[str, Any]:
    if not is_twitch_clip_request(text):
        return {"ok": False, "message": "Twitch切り抜き命令ではありません"}
    clips = clip_latest_twitch_stream(max_clips=max_clips)
    return {
        "ok": True,
        "message": f"Twitch配信から{len(clips)}本の切り抜きを作りました。",
        "clips": [str(p) for p in clips],
    }


if __name__ == "__main__":
    import sys
    command = " ".join(sys.argv[1:]) or "昨日の配信切り抜いて"
    result = run_twitch_clip_command(command)
    print(result["message"])
    for clip in result.get("clips", []):
        print(clip)
