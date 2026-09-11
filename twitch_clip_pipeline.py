from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "twitch_config.json"
DOWNLOAD_DIR = ROOT / "twitch_vods"
CLIPS_DIR = ROOT / "clips"
STATE_PATH = ROOT / "twitch_state.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"{CONFIG_PATH} がありません。twitch_config.example.json をコピーして設定してください。"
        )
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def twitch_app_token(config: dict) -> str:
    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "grant_type": "client_credentials",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_user_id(config: dict, token: str) -> str:
    response = requests.get(
        "https://api.twitch.tv/helix/users",
        headers={"Client-ID": config["client_id"], "Authorization": f"Bearer {token}"},
        params={"login": config["channel_login"]},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    if not data:
        raise RuntimeError("Twitchチャンネルが見つかりません")
    return data[0]["id"]


def get_latest_vod(config: dict) -> dict | None:
    token = twitch_app_token(config)
    user_id = get_user_id(config, token)
    response = requests.get(
        "https://api.twitch.tv/helix/videos",
        headers={"Client-ID": config["client_id"], "Authorization": f"Bearer {token}"},
        params={"user_id": user_id, "type": "archive", "first": 1},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    return data[0] if data else None


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def download_vod(vod: dict) -> Path:
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    vod_id = vod["id"]
    output = DOWNLOAD_DIR / f"{vod_id}.mp4"
    if output.exists():
        return output

    url = vod["url"]
    subprocess.run(
        ["yt-dlp", "--merge-output-format", "mp4", "-o", str(output), url],
        check=True,
    )
    return output


def clean_filename(text: str) -> str:
    return re.sub(r"[^0-9A-Za-zぁ-んァ-ヶ一-龯 _-]", "", text)[:80].strip() or "clip"


def make_clip(vod_path: Path, start_seconds: float, end_seconds: float, title: str, index: int) -> Path:
    CLIPS_DIR.mkdir(exist_ok=True)
    output = CLIPS_DIR / f"{vod_path.stem}_{index:02d}_{clean_filename(title)}.mp4"
    duration = max(1.0, end_seconds - start_seconds)
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", str(max(0, start_seconds)), "-i", str(vod_path),
            "-t", str(duration), "-c:v", "libx264", "-c:a", "aac", str(output)
        ],
        check=True,
    )
    return output


def process_latest_vod() -> Path | None:
    config = load_config()
    vod = get_latest_vod(config)
    if not vod:
        print("VODがありません")
        return None

    state = load_state()
    if state.get("last_vod_id") == vod["id"]:
        print(f"新しいVODなし: {vod['id']}")
        return None

    print(f"新しいVOD: {vod['id']} / {vod['title']}")
    path = download_vod(vod)
    state["last_vod_id"] = vod["id"]
    save_state(state)
    print(f"VOD取得完了: {path}")
    return path


if __name__ == "__main__":
    process_latest_vod()
