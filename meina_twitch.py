from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from twitch_ai_clipper import create_ai_clips
from twitch_clip_pipeline import download_vod, get_user_id, load_config, twitch_app_token

JST = timezone(timedelta(hours=9))


def is_twitch_clip_request(text: str) -> bool:
    compact = re.sub(r"\s+", "", text).lower()
    return (
        ("切り抜" in compact or "ハイライト" in compact)
        and ("配信" in compact or "twitch" in compact or "昨日" in compact or "今日" in compact or "最近" in compact)
    )


def _requested_day(text: str) -> str | None:
    compact = re.sub(r"\s+", "", text)
    if "昨日" in compact:
        return "yesterday"
    if "今日" in compact:
        return "today"
    return None


def _get_vods(config: dict[str, Any], day: str | None = None) -> list[dict[str, Any]]:
    token = twitch_app_token(config)
    user_id = get_user_id(config, token)
    now = datetime.now(JST)
    params: dict[str, Any] = {"user_id": user_id, "type": "archive", "first": 20}
    if day == "yesterday":
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        params["started_at"] = start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        params["ended_at"] = end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    elif day == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        params["started_at"] = start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    response = requests.get(
        "https://api.twitch.tv/helix/videos",
        headers={"Client-ID": config["client_id"], "Authorization": f"Bearer {token}"},
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def _select_vod(text: str) -> dict[str, Any] | None:
    config = load_config()
    day = _requested_day(text)
    vods = _get_vods(config, day)
    if vods:
        return vods[0]
    if day:
        return None
    return _get_vods(config)[0] if _get_vods(config) else None


def clip_twitch_stream(text: str, max_clips: int = 3) -> list[Path]:
    vod = _select_vod(text)
    if vod is None:
        raise RuntimeError("指定された日のTwitch VODが見つかりませんでした")
    print(f"VOD取得対象: {vod['id']} / {vod.get('title', '')}")
    vod_path = download_vod(vod)
    return create_ai_clips(vod_path, max_clips=max_clips)


def clip_latest_twitch_stream(max_clips: int = 3) -> list[Path]:
    return clip_twitch_stream("最近の配信を切り抜いて", max_clips=max_clips)


def run_twitch_clip_command(text: str, max_clips: int = 3) -> dict[str, Any]:
    if not is_twitch_clip_request(text):
        return {"ok": False, "message": "Twitch切り抜き命令ではありません"}
    clips = clip_twitch_stream(text, max_clips=max_clips)
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
