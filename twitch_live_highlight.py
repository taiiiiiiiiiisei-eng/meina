"""配信中の短い音声チャンクをWhisper + Ollamaで評価し、見どころ候補を保存する。"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "twitch_live_highlights"
MARKERS_PATH = OUTPUT_DIR / "candidates.jsonl"
CHUNK_SECONDS = max(10, int(os.getenv("MEINA_LIVE_HIGHLIGHT_CHUNK", "20")))
MIN_SCORE = max(0, min(100, int(os.getenv("MEINA_LIVE_HIGHLIGHT_MIN_SCORE", "65"))))
REFRESH_URL_SECONDS = max(60, int(os.getenv("MEINA_LIVE_HIGHLIGHT_URL_REFRESH", "300")))
LOCK_PATH = OUTPUT_DIR / "monitor.lock.json"
SHORTLIST_PATH = OUTPUT_DIR / "shortlist.json"
OLLAMA_URL = os.getenv("MEINA_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("MEINA_OLLAMA_MODEL", "meina")

HIGHLIGHT_WORDS = (
    "やば", "うま", "神", "えぐ", "クラッチ", "1v", "2k", "3k", "4k", "ace",
    "勝った", "逆転", "無理", "最高", "すご", "マジ", "笑", "www", "!?",
)


def _read_lock() -> dict[str, Any]:
    if not LOCK_PATH.exists():
        return {}
    try:
        data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _process_command_line(pid: int) -> str:
    if pid <= 0:
        return ""
    try:
        if os.name == "nt":
            command = (
                "$p = Get-CimInstance Win32_Process -Filter "
                f"'ProcessId = {pid}'; "
                "if ($p) { [Console]::Out.Write($p.CommandLine) }"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            return result.stdout.strip()
        proc_cmdline = Path(f"/proc/{pid}/cmdline")
        if proc_cmdline.exists():
            return proc_cmdline.read_bytes().decode("utf-8", errors="replace").replace("\x00", " ")
    except Exception:
        return ""
    return ""


def is_monitor_running() -> bool:
    data = _read_lock()
    try:
        pid = int(data.get("pid", 0))
    except (TypeError, ValueError):
        pid = 0
    if not _pid_is_running(pid):
        try:
            LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    command_line = _process_command_line(pid)
    script_path = str(Path(__file__).resolve())
    if command_line and script_path not in command_line:
        try:
            LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    return True


def _acquire_monitor_lock() -> bool:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "pid": os.getpid(),
        "script": str(Path(__file__).resolve()),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    for _ in range(2):
        try:
            fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            if is_monitor_running():
                return False
    return False


def _release_monitor_lock() -> None:
    try:
        LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def stop_monitor() -> bool:
    data = _read_lock()
    try:
        pid = int(data.get("pid", 0))
    except (TypeError, ValueError):
        pid = 0

    if not _pid_is_running(pid):
        _release_monitor_lock()
        return False

    command_line = _process_command_line(pid)
    script_path = str(Path(__file__).resolve())
    if not command_line or script_path not in command_line:
        return False

    try:
        if os.name == "nt":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                print(f"❌ taskkill失敗: {result.stderr.strip() or result.stdout.strip()}")
                return False
        else:
            os.kill(pid, 15)
        _release_monitor_lock()
        return True
    except Exception as exc:
        print(f"❌ ライブ見どころ監視の停止に失敗しました: {exc}")
        return False


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
    import requests

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
    stream_id: str = "",
) -> dict[str, Any]:
    if stream_started_at is not None:
        absolute_start = max(0.0, (chunk_started_at - stream_started_at).total_seconds() + segment_start)
        absolute_end = max(absolute_start, (chunk_started_at - stream_started_at).total_seconds() + segment_end)
    else:
        absolute_start = segment_start
        absolute_end = segment_end
    return {
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "stream_id": str(stream_id),
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

def load_candidates(limit: int = 5, stream_id: str | None = None) -> list[dict[str, Any]]:
    """保存済みの見どころ候補を新しい順に返す。"""
    limit = max(1, min(20, int(limit)))
    if not MARKERS_PATH.exists():
        return []
    candidates: list[dict[str, Any]] = []
    try:
        lines = MARKERS_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    for line in reversed(lines):
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        if stream_id and str(item.get("stream_id", "")) != str(stream_id):
            continue
        candidates.append(item)
        if len(candidates) >= limit:
            break
    return candidates


def format_candidates(candidates: list[dict[str, Any]], limit: int = 5) -> str:
    """音声応答しやすい見どころ一覧に整形する。"""
    items = candidates[: max(1, min(20, int(limit)))]
    if not items:
        return "保存されている見どころ候補はありません。"

    lines = [f"見どころ候補は{len(items)}件あります。"]
    for index, item in enumerate(items, 1):
        score = int(item.get("score", 0))
        start = float(item.get("stream_time_start", 0.0))
        title = str(item.get("title") or "配信ハイライト候補").strip()
        text_value = str(item.get("text") or "").strip().replace("\n", " ")
        if len(text_value) > 45:
            text_value = text_value[:45] + "…"
        minutes = int(start // 60)
        seconds = int(start % 60)
        lines.append(f"{index}番、{minutes}分{seconds}秒、評価{score}、{title}。{text_value}")
    return "\n".join(lines)

def _deduplicate_candidates(candidates: list[dict[str, Any]], gap_seconds: float = 20.0) -> list[dict[str, Any]]:
    """近すぎる候補をまとめ、同じ場面の重複選出を防ぐ。"""
    ranked = sorted(
        candidates,
        key=lambda item: (
            int(item.get("score", 0)),
            float(item.get("stream_time_start", 0.0)),
        ),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    for item in ranked:
        try:
            start = float(item.get("stream_time_start", 0.0))
        except (TypeError, ValueError):
            continue
        if any(abs(start - float(other.get("stream_time_start", -9999.0))) < gap_seconds for other in selected):
            continue
        selected.append(item)
    return selected


def _ai_select_shortlist(candidates: list[dict[str, Any]], limit: int) -> list[int]:
    import requests

    compact = [
        {
            "id": index,
            "time": round(float(item.get("stream_time_start", 0.0)), 1),
            "score": int(item.get("score", 0)),
            "title": str(item.get("title", ""))[:100],
            "reason": str(item.get("reason", ""))[:200],
            "text": str(item.get("text", ""))[:700],
        }
        for index, item in enumerate(candidates)
    ]
    schema = {
        "type": "object",
        "properties": {
            "selected_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "maxItems": limit,
            },
            "reason": {"type": "string"},
        },
        "required": ["selected_ids", "reason"],
    }
    prompt = (
        "あなたは日本語ゲーム配信の切り抜き担当AIです。候補一覧から、実際に短尺動画にした価値が高い場面を"
        f"{limit}件まで選んでください。既存scoreだけでなく、面白さ、驚き、上手さ、感情、話としての分かりやすさを重視します。"
        "同じ出来事や近い時間の候補は複数選ばず、別の場面を優先してください。"
        "文字起こしにない出来事は想像しないでください。JSONだけを返してください。\n"
        + json.dumps(compact, ensure_ascii=False)
    )
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": schema,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.1},
        },
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("message", {}).get("content", "{}")
    data = json.loads(content)
    ids = data.get("selected_ids", [])
    if not isinstance(ids, list):
        raise ValueError("Ollamaの選定結果が不正です")
    return [int(item) for item in ids if isinstance(item, int)]


def shortlist_candidates(limit: int = 3) -> list[dict[str, Any]]:
    """保存済み候補から、AIで切り抜き価値の高い場面を再選定する。"""
    limit = max(1, min(5, int(limit)))
    candidates = load_candidates(limit=50)
    if not candidates:
        return []

    active_stream_id = next(
        (
            str(item.get("stream_id", "")).strip()
            for item in candidates
            if str(item.get("stream_id", "")).strip()
        ),
        "",
    )
    if active_stream_id:
        candidates = [
            item
            for item in candidates
            if str(item.get("stream_id", "")).strip() == active_stream_id
        ]

    pool = _deduplicate_candidates(candidates)[:15]
    selected: list[dict[str, Any]] = []
    used_ai_selection = False

    try:
        selected_ids = _ai_select_shortlist(pool, limit)
        seen: set[int] = set()
        for candidate_id in selected_ids:
            if not 0 <= candidate_id < len(pool) or candidate_id in seen:
                continue
            seen.add(candidate_id)
            selected.append(pool[candidate_id])
            if len(selected) >= limit:
                break
        used_ai_selection = bool(selected)
    except Exception as exc:
        print(f"⚠️ 見どころ再選定をスコア順へフォールバックします: {exc}")

    if not selected:
        selected = pool[:limit]

    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(candidates),
        "pool_count": len(pool),
        "selection_source": "score_fallback",
        "shortlist": selected,
    }
    if used_ai_selection:
        result["selection_source"] = "ollama"
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        SHORTLIST_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    return selected


def format_shortlist(candidates: list[dict[str, Any]]) -> str:
    """AIが選んだ見どころを音声向けに整形する。"""
    if not candidates:
        return "おすすめできる見どころ候補はまだありません。"
    lines = [f"おすすめの見どころは{len(candidates)}件です。"]
    for index, item in enumerate(candidates, 1):
        score = int(item.get("score", 0))
        start = float(item.get("stream_time_start", 0.0))
        title = str(item.get("title") or "配信ハイライト候補").strip()
        minutes = int(start // 60)
        seconds = int(start % 60)
        lines.append(f"{index}番、{minutes}分{seconds}秒、評価{score}、{title}。")
    return "\n".join(lines)


def _get_live_stream(config: dict[str, Any], token: str, user_id: str) -> dict[str, Any] | None:
    import requests

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

def _monitor_live_highlights_loop() -> None:
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
                    stream_id,
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

def monitor_live_highlights() -> None:
    """ライブ見どころ監視を1プロセスだけ実行する。"""
    if not _acquire_monitor_lock():
        print("⚠️ ライブ見どころ監視はすでに起動しています")
        return
    try:
        _monitor_live_highlights_loop()
    finally:
        _release_monitor_lock()


def start_monitor() -> bool:
    """固定スクリプトとしてライブ見どころ監視を起動する。"""
    env = os.environ.copy()
    command = [sys.executable, str(Path(__file__).resolve())]
    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    try:
        subprocess.Popen(command, cwd=str(ROOT), env=env, creationflags=creationflags)
        return True
    except Exception as exc:
        print(f"❌ ライブ見どころ監視の起動に失敗しました: {exc}")
        return False


if __name__ == "__main__":
    monitor_live_highlights()
