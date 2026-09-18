from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from meina_twitch_intent import is_twitch_clip_request, requested_day

try:
    import requests
except ImportError:  # 判定系テストでは外部通信ライブラリを必須にしない
    requests = None

from twitch_ai_clipper import create_ai_clips, create_shortlist_clips
from twitch_clip_pipeline import download_vod, get_user_id, load_config, twitch_app_token

JST = timezone(timedelta(hours=9))


# Backward-compatible private helper name used by existing tests/code.
def _requested_day(text: str) -> str | None:
    return requested_day(text)


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
    if requests is None:
        raise RuntimeError("Twitch APIを使うには requests が必要です")
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


def clip_shortlist_twitch_stream(max_clips: int = 3) -> list[Path]:
    """最新VODへ、配信中にAI選定したショートリストだけを適用する。"""
    config = load_config()
    vods = _get_vods(config)
    if not vods:
        raise RuntimeError("Twitchの最新VODが見つかりませんでした")
    vod = vods[0]
    print(f"AIおすすめ切り抜き対象: {vod['id']} / {vod.get('title', '')}")
    vod_path = download_vod(vod)
    return create_shortlist_clips(vod_path, max_clips=max_clips, vod=vod)


def run_shortlist_twitch_command(max_clips: int = 3) -> dict[str, Any]:
    clips = clip_shortlist_twitch_stream(max_clips=max_clips)
    queue_path = None
    try:
        from twitch_publish_queue import prepare_publish_queue
        queue_result = prepare_publish_queue(
            Path(clips[0]).parent.parent / "twitch_clip_results" / f"{Path(clips[0]).stem.rsplit('_', 1)[0]}_shortlist.json"
        )
        queue_path = queue_result.get("markdown_path")
    except Exception as exc:
        print(f"⚠️ おすすめ切り抜きの投稿準備キュー生成をスキップしました: {exc}")

    message = f"AIおすすめ候補から{len(clips)}本の切り抜きを作りました。"
    if queue_path:
        message += "投稿用の準備も完了しました。"
    return {
        "ok": True,
        "message": message,
        "clips": [str(p) for p in clips],
        "publish_queue": queue_path,
    }


def run_twitch_clip_command(text: str, max_clips: int = 3) -> dict[str, Any]:
    if not is_twitch_clip_request(text):
        return {"ok": False, "message": "Twitch切り抜き命令ではありません"}
    clips = clip_twitch_stream(text, max_clips=max_clips)
    queue_path = None
    try:
        from twitch_publish_queue import prepare_publish_queue
        queue_result = prepare_publish_queue()
        queue_path = queue_result.get("markdown_path")
    except Exception as exc:
        print(f"⚠️ 投稿準備キュー生成をスキップしました: {exc}")

    message = f"Twitch配信から{len(clips)}本の切り抜きを作りました。"
    if queue_path:
        message += "投稿用の準備も完了しました。"

    return {
        "ok": True,
        "message": message,
        "clips": [str(p) for p in clips],
        "publish_queue": queue_path,
    }


if __name__ == "__main__":
    import sys
    command = " ".join(sys.argv[1:]) or "昨日の配信切り抜いて"
    result = run_twitch_clip_command(command)
    print(result["message"])
    for clip in result.get("clips", []):
        print(clip)
