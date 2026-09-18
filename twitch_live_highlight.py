"""配信中の短い音声チャンクをWhisper + Ollamaで評価し、見どころ候補を保存する。"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "twitch_live_highlights"
MARKERS_PATH = OUTPUT_DIR / "candidates.jsonl"
CHUNK_SECONDS = max(10, int(os.getenv("MEINA_LIVE_HIGHLIGHT_CHUNK", "20")))
MIN_SCORE = max(0, min(100, int(os.getenv("MEINA_LIVE_HIGHLIGHT_MIN_SCORE", "65"))))
REFRESH_URL_SECONDS = max(60, int(os.getenv("MEINA_LIVE_HIGHLIGHT_URL_REFRESH", "300")))
OLLAMA_URL = os.getenv("MEINA_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("MEINA_OLLAMA_MODEL", "meina")

HIGHLIGHT_WORDS = (
    "やば", "うま", "神", "えぐ", "クラッチ", "1v", "2k", "3k", "4k", "ace",
    "勝った", "逆転", "無理", "最高", "すご", "マジ", "笑", "www", "!?",
)

def heuristic_score(text: str) -> int:
    compact = str(text or "").strip().lower()
    if not compact:
        return 0
    score = 20
    score += min(35, sum(8 for word in HIGHLIGHT_WORDS if word in compact))
    if len(compact) >= 60:
        score += 10
    if any(mark in compact for mark in ("!", "！", "?", "？")):
        score += 8
    if any(word in compact for word in ("ありがとう", "ナイス", "gg")):
        score += 4
    return max(0, min(100, score))

def score_transcript(text: str) -> dict[str, Any]:
    fallback = {
        "score": heuristic_score(text),
        "title": "配信ハイライト候補",
        "reason": "音声の内容から盛り上がりの可能性を検出しました。",
        "source": "heuristic",
    }
    try:
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "title": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["score", "title", "reason"],
        }
        prompt = (
            "日本語ゲーム配信の短い音声文字起こしを見て、切り抜き候補としての価値を0-100で評価してください。"
            "上手いプレイ、驚き、逆転、クラッチ、面白い反応、強い感情があれば高くしてください。"
            "文字起こしにない出来事を想像しないでください。JSONだけを返してください。\n"
            + str(text or "")[:1200]
        )
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "format": schema,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"temperature": 0.2},
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        data = json.loads(payload.get("message", {}).get("content", "{}"))
        score = max(0, min(100, int(data.get("score", fallback["score"]))))
        return {
            "score": score,
            "title": str(data.get("title") or fallback["title"])[:80],
            "reason": str(data.get("reason") or fallback["reason"])[:300],
            "source": "ollama",
        }
    except Exception as exc:
        print(f"⚠️ ライブAI判定をフォールバックします: {exc}")
        return fallback

def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def build_candidate(
    chunk_started_at: datetime,
    stream_started_at: datetime | None,
    segment_start: float,
    segment_end: float,
    text: str,
    decision: dict[str, Any],
) -> dict[str, Any]:
    if stream_started_at is not None:
        absolute_start = max(0.0, (chunk_started_at - stream_started_at).total_seconds() + segment_start)
        absolute_end = max(absolute_start, (chunk_started_at - stream_started_at).total_seconds() + segment_end)
    else:
        absolute_start = segment_start
        absolute_end = segment_end
    return {
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "stream_time_start": round(absolute_start, 2),
        "stream_time_end": round(absolute_end, 2),
        "text": str(text).strip(),
        "score": int(decision.get("score", 0)),
        "title": str(decision.get("title", "配信ハイライト候補")),
        "reason": str(decision.get("reason", "")),
        "source": str(decision.get("source", "unknown")),
    }

def append_candidate(candidate: dict[str, Any]) -> bool:
    if int(candidate.get("score", 0)) < MIN_SCORE:
        return False
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if MARKERS_PATH.exists():
        for line in MARKERS_PATH.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    existing.append(item)
            except json.JSONDecodeError:
                continue
    start = float(candidate.get("stream_time_start", 0.0))
    if any(abs(float(item.get("stream_time_start", -9999.0)) - start) < 15.0 for item in existing):
        return False
    with MARKERS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(candidate, ensure_ascii=False) + "\n")
    return True

def _get_live_stream(config: dict[str, Any], token: str, user_id: str) -> dict[str, Any] | None:
    response = requests.get(
        "https://api.twitch.tv/helix/streams",
        headers={"Client-ID": config["client_id"], "Authorization": f"Bearer {token}"},
        params={"user_id": user_id},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    return data[0] if data else None


def _resolve_audio_url(channel_login: str) -> str:
    result = subprocess.run(
        ["yt-dlp", "-g", "-f", "bestaudio/best", f"https://www.twitch.tv/{channel_login}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    urls = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not urls:
        raise RuntimeError("Twitchライブ音声URLを取得できませんでした")
    return urls[-1]

def _record_chunk(audio_url: str, output: Path, seconds: int) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", audio_url,
            "-t", str(seconds),
            "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(output),
        ],
        check=True,
        timeout=seconds + 45,
    )

def _transcribe_chunk(audio_path: Path) -> list[dict[str, Any]]:
    from faster_whisper import WhisperModel
    model_name = os.getenv("MEINA_WHISPER_MODEL", "large-v3")
    device = os.getenv("MEINA_WHISPER_DEVICE", "cuda")
    compute_type = os.getenv("MEINA_WHISPER_COMPUTE_TYPE", "float16")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(str(audio_path), language="ja", vad_filter=True, condition_on_previous_text=False)
    return [
        {"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()}
        for seg in segments
        if seg.text.strip()
    ]

def monitor_live_highlights() -> None:
    from twitch_clip_pipeline import get_user_id, load_config, twitch_app_token

    config = load_config()
    channel_login = str(config["channel_login"]).strip()
    if not channel_login:
        raise ValueError("channel_login が設定されていません")
    token = twitch_app_token(config)
    user_id = get_user_id(config, token)
    audio_url = ""
    audio_url_refreshed_at = 0.0
    stream_id = ""
    stream_started_at: datetime | None = None
    print("🤖 めいな ライブ見どころ監視を開始")
    print(f"🎧 {CHUNK_SECONDS}秒ごとに音声を解析します。候補閾値={MIN_SCORE}")

    while True:
        chunk_started_at = datetime.now(timezone.utc)
        try:
            stream = _get_live_stream(config, token, user_id)
            if not stream:
                audio_url = ""
                stream_id = ""
                stream_started_at = None
                print("⏭️ 現在は配信していません")
                time.sleep(15)
                continue

            current_stream_id = str(stream.get("id", ""))
            current_started_at = _parse_time(str(stream.get("started_at", "")))
            if current_stream_id != stream_id:
                stream_id = current_stream_id
                stream_started_at = current_started_at
                audio_url = ""
                audio_url_refreshed_at = 0.0
                print(f"🔴 配信音声解析を開始: stream_id={stream_id}")

            now = time.time()
            if not audio_url or now - audio_url_refreshed_at >= REFRESH_URL_SECONDS:
                audio_url = _resolve_audio_url(channel_login)
                audio_url_refreshed_at = now
            with tempfile.TemporaryDirectory(prefix="meina_live_audio_") as tmp:
                audio_path = Path(tmp) / "chunk.wav"
                _record_chunk(audio_url, audio_path, CHUNK_SECONDS)
                segments = _transcribe_chunk(audio_path)
            for segment in segments:
                decision = score_transcript(segment["text"])
                candidate = build_candidate(
                    chunk_started_at,
                    stream_started_at,
                    segment["start"],
                    segment["end"],
                    segment["text"],
                    decision,
                )
                if append_candidate(candidate):
                    print(f"⭐ 見どころ候補: {candidate['score']} / {candidate['title']} / {candidate['text']}")
        except KeyboardInterrupt:
            print("\n停止しました")
            return
        except Exception as exc:
            print(f"⚠️ ライブ見どころ監視エラー: {exc}")
            audio_url = ""
            time.sleep(5)

def start_monitor() -> bool:
    """固定スクリプトとしてライブ見どころ監視を起動する。"""
    env = os.environ.copy()
    command = [os.sys.executable, str(Path(__file__).resolve())]
    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    try:
        subprocess.Popen(command, cwd=str(ROOT), env=env, creationflags=creationflags)
        return True
    except Exception as exc:
        print(f"❌ ライブ見どころ監視の起動に失敗しました: {exc}")
        return False


if __name__ == "__main__":
    monitor_live_highlights()
