"""Twitch配信中の状態を監視し、配信終了後にV2切り抜きを起動する。"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from twitch_auto_clip_v2 import process_new_vod
from twitch_clip_pipeline import get_user_id, load_config, twitch_app_token

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "twitch_live_state.json"
INTERVAL = max(10, int(os.getenv("MEINA_TWITCH_LIVE_INTERVAL", "30")))
POST_OFFLINE_DELAY = max(0, int(os.getenv("MEINA_TWITCH_POST_OFFLINE_DELAY", "30")))
PROCESS_OFFLINE_STARTUP = os.getenv("MEINA_TWITCH_PROCESS_OFFLINE_STARTUP", "0").strip().lower() in {"1", "true", "yes", "on"}

def load_live_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_live_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def get_current_stream(config: dict[str, Any], token: str, user_id: str) -> dict[str, Any] | None:
    response = requests.get(
        "https://api.twitch.tv/helix/streams",
        headers={"Client-ID": config["client_id"], "Authorization": f"Bearer {token}"},
        params={"user_id": user_id},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    return data[0] if data else None

def stream_transition(was_live: bool, current_stream: dict[str, Any] | None) -> str:
    now_live = current_stream is not None
    if not was_live and now_live:
        return "started"
    if was_live and not now_live:
        return "ended"
    if now_live:
        return "live"
    return "offline"

def run_live_monitor() -> None:
    config = load_config()
    token = twitch_app_token(config)
    user_id = get_user_id(config, token)
    state = load_live_state()
    was_live = bool(state.get("was_live"))
    tracked_stream_id = str(state.get("stream_id", ""))

    print("🤖 めいな Twitchライブ監視を開始")
    print(f"⏱️ {INTERVAL}秒ごとに配信状態を確認します")

    while True:
        try:
            stream = get_current_stream(config, token, user_id)
            transition = stream_transition(was_live, stream)

            if transition == "started":
                tracked_stream_id = str(stream.get("id", ""))
                started_at = str(stream.get("started_at", ""))
                state = {
                    "was_live": True,
                    "stream_id": tracked_stream_id,
                    "started_at": started_at,
                    "last_seen_at": datetime.now(timezone.utc).isoformat(),
                }
                save_live_state(state)
                print(f"🔴 配信開始を検知: stream_id={tracked_stream_id}")
            elif transition == "live":
                print(f"🔴 配信中: stream_id={stream.get('id', tracked_stream_id)}")
            elif transition == "ended":
                ended_stream_id = tracked_stream_id or str(state.get("stream_id", ""))
                print(f"🟢 配信終了を検知: stream_id={ended_stream_id}")
                if POST_OFFLINE_DELAY:
                    print(f"⏳ VOD反映待ち: {POST_OFFLINE_DELAY}秒")
                    time.sleep(POST_OFFLINE_DELAY)
                clips = process_new_vod()
                for clip in clips or []:
                    print(f"✅ 切り抜き完成: {clip}")
                state = {
                    "was_live": False,
                    "stream_id": ended_stream_id,
                    "last_completed_stream_id": ended_stream_id,
                    "last_seen_at": datetime.now(timezone.utc).isoformat(),
                }
                save_live_state(state)
                was_live = False
                tracked_stream_id = ended_stream_id
            else:
                if not was_live and PROCESS_OFFLINE_STARTUP:
                    clips = process_new_vod()
                    for clip in clips or []:
                        print(f"✅ オフライン時の新規VOD切り抜き完成: {clip}")
                state["was_live"] = False
                state["last_seen_at"] = datetime.now(timezone.utc).isoformat()
                save_live_state(state)

            if transition != "ended":
                was_live = stream is not None

        except KeyboardInterrupt:
            print("\n停止しました")
            return
        except Exception as exc:
            print(f"⚠️ Twitchライブ監視エラー: {exc}")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    run_live_monitor()
