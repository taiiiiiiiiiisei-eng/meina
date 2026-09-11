import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import requests


BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "twitch_vods"
CLIP_DIR = BASE_DIR / "clips"
STATE_FILE = BASE_DIR / "twitch_clipper_state.json"

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API = "https://api.twitch.tv/helix"


class TwitchClipper:
    """Twitch VOD取得 + 文字起こし + AI候補選定 + FFmpeg切り抜きのMVP。"""

    def __init__(self, channel: str | None = None):
        self.channel = channel or os.getenv("TWITCH_CHANNEL", "").strip()
        self.client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("TWITCH_CLIENT_SECRET", "").strip()
        self.download_dir = Path(os.getenv("MEINA_VOD_DIR", str(DOWNLOAD_DIR)))
        self.clip_dir = Path(os.getenv("MEINA_CLIP_DIR", str(CLIP_DIR)))
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.clip_dir.mkdir(parents=True, exist_ok=True)

    def _require_config(self) -> None:
        missing = []
        if not self.channel:
            missing.append("TWITCH_CHANNEL")
        if not self.client_id:
            missing.append("TWITCH_CLIENT_ID")
        if not self.client_secret:
            missing.append("TWITCH_CLIENT_SECRET")
        if missing:
            raise RuntimeError("Twitch設定が不足しています: " + ", ".join(missing))

    def _app_token(self) -> str:
        response = requests.post(
            TWITCH_TOKEN_URL,
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _headers(self, token: str) -> dict[str, str]:
        return {"Client-ID": self.client_id, "Authorization": f"Bearer {token}"}

    def get_broadcaster_id(self, token: str) -> str:
        response = requests.get(
            f"{TWITCH_API}/users",
            headers=self._headers(token),
            params={"login": self.channel},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            raise RuntimeError(f"Twitchチャンネルが見つかりません: {self.channel}")
        return data[0]["id"]

    def latest_vod(self) -> dict[str, Any] | None:
        self._require_config()
        token = self._app_token()
        broadcaster_id = self.get_broadcaster_id(token)
        response = requests.get(
            f"{TWITCH_API}/videos",
            headers=self._headers(token),
            params={
                "user_id": broadcaster_id,
                "type": "archive",
                "first": 5,
            },
            timeout=20,
        )
        response.raise_for_status()
        videos = response.json().get("data", [])
        return videos[0] if videos else None

    def _load_state(self) -> dict[str, Any]:
        if not STATE_FILE.exists():
            return {}
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self, state: dict[str, Any]) -> None:
        STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def is_new_vod(self, vod: dict[str, Any]) -> bool:
        return self._load_state().get("last_vod_id") != vod.get("id")

    def mark_processed(self, vod: dict[str, Any]) -> None:
        self._save_state({
            "last_vod_id": vod.get("id"),
            "last_vod_url": vod.get("url"),
            "last_processed_at": int(time.time()),
        })

    def download_vod(self, vod_url: str, vod_id: str) -> Path:
        """yt-dlpでVODを取得。yt-dlpが必要。"""
        output = self.download_dir / f"vod_{vod_id}.%(ext)s"
        existing = list(self.download_dir.glob(f"vod_{vod_id}.*"))
        if existing:
            return existing[0]

        command = [
            "yt-dlp",
            "--no-playlist",
            "--merge-output-format", "mp4",
            "-o", str(output),
            vod_url,
        ]
        subprocess.run(command, check=True)
        existing = list(self.download_dir.glob(f"vod_{vod_id}.*"))
        if not existing:
            raise RuntimeError("VODのダウンロード後にファイルが見つかりませんでした")
        return existing[0]

    def transcribe(self, video_path: Path) -> list[dict[str, Any]]:
        """faster-whisperで字幕相当のタイムスタンプ付き文字起こしを作る。"""
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper がインストールされていません") from exc

        model_name = os.getenv("MEINA_WHISPER_MODEL", "large-v3")
        device = os.getenv("MEINA_WHISPER_DEVICE", "cuda")
        compute_type = os.getenv("MEINA_WHISPER_COMPUTE_TYPE", "float16")
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        segments, _ = model.transcribe(str(video_path), language="ja", vad_filter=True)

        result = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                result.append({
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": text,
                })
        transcript_path = video_path.with_suffix(".json")
        transcript_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

    def find_candidates(self, transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """まずは軽量な日本語リアクション語スコアで候補を作る。"""
        patterns = [
            r"ｗ+", r"笑", r"草", r"やば", r"えぐ", r"うそ", r"まじ", r"なんで",
            r"うわ", r"えっ", r"は？", r"きた", r"ナイス", r"神", r"勝った", r"負けた",
            r"惜し", r"キャリー", r"ACE", r"エース",
        ]
        candidates = []
        for index, seg in enumerate(transcript):
            text = seg["text"]
            score = sum(1 for pattern in patterns if re.search(pattern, text, re.I))
            if score == 0:
                continue
            start = max(0.0, seg["start"] - 12.0)
            end = seg["end"] + 18.0
            candidates.append({
                "index": index,
                "start": start,
                "end": end,
                "score": score,
                "text": text,
            })
        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates[:20]

    def ask_ollama(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Ollamaに候補を順位付けさせる。失敗時は元のスコア順を返す。"""
        try:
            import ollama
        except ImportError:
            return candidates[:5]

        model = os.getenv("MEINA_CLIP_MODEL", "meina")
        compact = [
            {"id": i, "start": round(c["start"], 1), "end": round(c["end"], 1), "text": c["text"]}
            for i, c in enumerate(candidates)
        ]
        prompt = (
            "配信切り抜き候補を評価してください。日本語配信です。"
            "視聴者が見て面白い、驚く、笑う、上手いと思う場面を優先してください。"
            "必ずJSON配列だけを返し、各要素は {id, score} としてください。scoreは0-100。\n"
            + json.dumps(compact, ensure_ascii=False)
        )
        try:
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            content = response["message"]["content"]
            match = re.search(r"\[[\s\S]*\]", content)
            if not match:
                return candidates[:5]
            ranked = json.loads(match.group(0))
            by_id = {i: c for i, c in enumerate(candidates)}
            result = []
            for item in ranked:
                candidate = by_id.get(int(item.get("id", -1)))
                if candidate:
                    candidate = dict(candidate)
                    candidate["ai_score"] = float(item.get("score", 0))
                    result.append(candidate)
            result.sort(key=lambda x: x.get("ai_score", 0), reverse=True)
            return result[:5] or candidates[:5]
        except Exception as exc:
            print(f"⚠️ Ollama評価をスキップ: {exc}")
            return candidates[:5]

    def make_clip(self, video_path: Path, start: float, end: float, index: int) -> Path:
        output = self.clip_dir / f"clip_{video_path.stem}_{index:02d}.mp4"
        command = [
            "ffmpeg", "-y",
            "-ss", f"{start:.2f}",
            "-i", str(video_path),
            "-t", f"{max(1.0, end - start):.2f}",
            "-c:v", "libx264",
            "-c:a", "aac",
            str(output),
        ]
        subprocess.run(command, check=True)
        return output

    def process_latest(self) -> dict[str, Any]:
        vod = self.latest_vod()
        if not vod:
            return {"status": "no_vod"}
        if not self.is_new_vod(vod):
            return {"status": "already_processed", "vod": vod}

        print(f"🎥 新しいVOD: {vod['url']}")
        video = self.download_vod(vod["url"], vod["id"])
        transcript = self.transcribe(video)
        candidates = self.find_candidates(transcript)
        ranked = self.ask_ollama(candidates)
        clips = []
        for index, candidate in enumerate(ranked[:3], start=1):
            clips.append(str(self.make_clip(video, candidate["start"], candidate["end"], index)))
        self.mark_processed(vod)
        return {"status": "completed", "vod": vod, "video": str(video), "clips": clips}


if __name__ == "__main__":
    result = TwitchClipper().process_latest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
