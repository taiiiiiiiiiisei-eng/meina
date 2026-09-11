from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests

from twitch_clip_pipeline import make_clip, transcribe_vod, _duration_seconds

ROOT = Path(__file__).resolve().parent
CLIPS_DIR = ROOT / "clips"
RESULT_DIR = ROOT / "twitch_clip_results"
OLLAMA_URL = os.getenv("MEINA_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("MEINA_OLLAMA_MODEL", "meina")


def _candidate_windows(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for i, seg in enumerate(segments):
        start = max(0.0, float(seg["start"]) - 8.0)
        end = min(float(segments[-1]["end"]), float(seg["end"]) + 15.0)
        texts = [seg["text"]]
        j = i + 1
        while j < len(segments) and float(segments[j]["start"]) <= end:
            texts.append(segments[j]["text"])
            end = min(float(segments[-1]["end"]), float(segments[j]["end"]) + 8.0)
            j += 1
        text = " ".join(texts).strip()
        if len(text) < 8:
            continue
        score = 0
        for word in ("やば", "うま", "神", "えぐ", "勝った", "負け", "キル", "クラッチ", "www", "笑", "なんで", "無理", "最高", "すご", "マジ"):
            if word in text:
                score += 1
        windows.append({"start": start, "end": min(start + 55.0, end), "text": text, "heuristic": score})
    windows.sort(key=lambda x: x["heuristic"], reverse=True)
    unique: list[dict[str, Any]] = []
    for item in windows:
        if any(abs(item["start"] - x["start"]) < 20 for x in unique):
            continue
        unique.append(item)
        if len(unique) >= 15:
            break
    return unique


def _ask_ollama(candidates: list[dict[str, Any]], max_clips: int) -> list[dict[str, Any]]:
    compact = [
        {"id": i, "start": round(c["start"], 1), "end": round(c["end"], 1), "text": c["text"][:900]}
        for i, c in enumerate(candidates)
    ]

    # OllamaのJSON modeは配列を直接返すとは限らないため、最上位をobjectに固定し、
    # clips配列の中に必要な選択結果を入れさせる。
    schema = {
        "type": "object",
        "properties": {
            "clips": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "reason": {"type": "string"},
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    },
                    "required": ["id", "title", "reason", "score"],
                },
                "maxItems": max_clips,
            }
        },
        "required": ["clips"],
    }

    prompt = (
        "あなたは日本語配信の切り抜き編集者です。以下の候補から、視聴者が面白い・驚く・上手い・"
        "感情が動くと思う場面を最大" + str(max_clips) + "個選んでください。VALORANT等のゲーム配信を想定。\n"
        "必ずJSONオブジェクトを返し、clips配列に選択結果を入れてください。"
        "各要素は候補id、短い日本語タイトル、選んだ理由、0-100のscoreを含めてください。\n"
        "候補:\n" + json.dumps(compact, ensure_ascii=False)
    )

    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": schema,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.2},
        },
        timeout=120,
    )
    r.raise_for_status()
    payload = r.json()
    content = payload.get("message", {}).get("content", "")

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # 念のためJSON部分だけを復旧する。
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            raise RuntimeError("Ollamaが有効なJSONを返しませんでした")
        data = json.loads(match.group(0))

    if isinstance(data, list):
        selected = data
    elif isinstance(data, dict) and isinstance(data.get("clips"), list):
        selected = data["clips"]
    elif isinstance(data, dict) and isinstance(data.get("answer"), str):
        # 古いモデルがanswer形式を返した場合でも、候補本文との一致から1件だけ復旧する。
        answer = data["answer"].strip()
        selected = []
        for i, candidate in enumerate(candidates):
            if answer and answer in candidate["text"]:
                selected.append({
                    "id": i,
                    "title": "AI選出ハイライト",
                    "reason": "Ollamaが候補本文を選択しました。",
                    "score": 70,
                })
                break
    else:
        selected = []

    valid: list[dict[str, Any]] = []
    for item in selected:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            continue
        if not 0 <= item["id"] < len(candidates):
            continue
        item["score"] = max(0, min(100, int(item.get("score", 0))))
        valid.append(item)

    if not valid:
        raise RuntimeError("Ollamaから切り抜き候補を1件も選べませんでした")
    return valid


def create_ai_clips(vod_path: Path, max_clips: int = 3) -> list[Path]:
    segments = transcribe_vod(vod_path)
    if not segments:
        raise RuntimeError("音声から字幕を取得できませんでした")

    candidates = _candidate_windows(segments)
    if not candidates:
        raise RuntimeError("切り抜き候補を作れませんでした")

    selected = _ask_ollama(candidates, max_clips)
    selected.sort(key=lambda x: int(x.get("score", 0)), reverse=True)

    RESULT_DIR.mkdir(exist_ok=True)
    results: list[dict[str, Any]] = []
    outputs: list[Path] = []
    duration = _duration_seconds(vod_path)

    for index, item in enumerate(selected[:max_clips], 1):
        cid = item["id"]
        c = candidates[cid]
        start = max(0.0, min(c["start"], duration - 1.0))
        end = max(start + 8.0, min(c["end"], duration))
        title = str(item.get("title") or f"切り抜き{index}")
        path = make_clip(vod_path, start, end, title, index)
        outputs.append(path)
        results.append({
            "file": str(path),
            "start": start,
            "end": end,
            "title": title,
            "reason": item.get("reason", ""),
            "score": item.get("score", 0),
            "transcript": c["text"],
        })

    (RESULT_DIR / f"{vod_path.stem}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return outputs


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python twitch_ai_clipper.py twitch_vods/VIDEO.mp4")
    paths = create_ai_clips(Path(sys.argv[1]))
    for path in paths:
        print(f"完成: {path}")
