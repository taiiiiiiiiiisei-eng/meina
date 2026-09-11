from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import requests
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "twitch_config.json"
DOWNLOAD_DIR = ROOT / "twitch_vods"
CLIPS_DIR = ROOT / "clips"
STATE_PATH = ROOT / "twitch_state.json"
TRANSCRIPT_DIR = ROOT / "twitch_transcripts"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"{CONFIG_PATH} がありません。twitch_config.example.json をコピーして設定してください。")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def twitch_app_token(config: dict[str, Any]) -> str:
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


def get_user_id(config: dict[str, Any], token: str) -> str:
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


def get_latest_vod(config: dict[str, Any]) -> dict[str, Any] | None:
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


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def download_vod(vod: dict[str, Any]) -> Path:
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    vod_id = str(vod["id"])
    output = DOWNLOAD_DIR / f"{vod_id}.mp4"
    if output.exists():
        return output

    subprocess.run(
        ["yt-dlp", "--merge-output-format", "mp4", "-o", str(output), vod["url"]],
        check=True,
    )
    return output


def clean_filename(text: str) -> str:
    return re.sub(r"[^0-9A-Za-zぁ-んァ-ヶ一-龯 _-]", "", text)[:80].strip() or "clip"


def make_clip(vod_path: Path, start_seconds: float, end_seconds: float, title: str, index: int) -> Path:
    CLIPS_DIR.mkdir(exist_ok=True)
    start = max(0.0, float(start_seconds))
    end = max(start + 1.0, float(end_seconds))
    output = CLIPS_DIR / f"{vod_path.stem}_{index:02d}_{clean_filename(title)}.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", str(start), "-i", str(vod_path),
            "-t", str(end - start), "-c:v", "libx264", "-c:a", "aac", str(output),
        ],
        check=True,
    )
    return output


def _duration_seconds(vod_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(vod_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def transcribe_vod(vod_path: Path) -> list[dict[str, Any]]:
    TRANSCRIPT_DIR.mkdir(exist_ok=True)
    transcript_path = TRANSCRIPT_DIR / f"{vod_path.stem}.json"
    if transcript_path.exists():
        return json.loads(transcript_path.read_text(encoding="utf-8"))

    audio_path = TRANSCRIPT_DIR / f"{vod_path.stem}.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(vod_path), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(audio_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    model_name = os.getenv("MEINA_WHISPER_MODEL", "large-v3")
    device = os.getenv("MEINA_WHISPER_DEVICE", "cuda")
    compute_type = os.getenv("MEINA_WHISPER_COMPUTE_TYPE", "float16")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(str(audio_path), language="ja", vad_filter=True)
    result = [
        {"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()}
        for seg in segments
        if seg.text.strip()
    ]
    transcript_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def process_latest_vod(download_only: bool = False) -> Path | None:
    config = load_config()
    vod = get_latest_vod(config)
    if not vod:
        print("VODがありません")
        return None

    state = load_state()
    existing = DOWNLOAD_DIR / f"{vod['id']}.mp4"
    if state.get("last_vod_id") == vod["id"] and not download_only:
        if existing.exists():
            return existing
        print(f"新しいVODなし: {vod['id']}")
        return None

    print(f"VOD取得対象: {vod['id']} / {vod.get('title', '')}")
    path = download_vod(vod)
    if not download_only:
        state["last_vod_id"] = vod["id"]
        save_state(state)
    print(f"VOD取得完了: {path}")
    return path


if __name__ == "__main__":
    process_latest_vod()
