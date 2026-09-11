from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests

from twitch_clip_pipeline import make_clip, transcribe_vod, _duration_seconds
from twitch_video_editor import edit_generated_clip

ROOT = Path(__file__).resolve().parent
CLIPS_DIR = ROOT / "clips"
RESULT_DIR = ROOT / "twitch_clip_results"
OLLAMA_URL = os.getenv("MEINA_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("MEINA_OLLAMA_MODEL", "meina")
MIN_CLIP_GAP_SECONDS = 5.0


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
    selection_limit = min(len(candidates), max(max_clips * 3, max_clips))
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
                "maxItems": selection_limit,
            }
        },
        "required": ["clips"],
    }
    prompt = (
        "あなたは日本語配信の切り抜き編集者です。以下の候補から、視聴者が面白い・驚く・上手い・"
        "感情が動くと思う場面を最大" + str(selection_limit) + "個選んでください。VALORANT等のゲーム配信を想定。\n"
        "重要: 同じ出来事やほぼ同じ時間帯の候補はできるだけ選ばず、配信内の別々の場面を優先してください。"
        "最終的には別々の場面から最大" + str(max_clips) + "本を作ります。\n"
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
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            raise RuntimeError("Ollamaが有効なJSONを返しませんでした")
        data = json.loads(match.group(0))

    if isinstance(data, list):
        selected = data
    elif isinstance(data, dict) and isinstance(data.get("clips"), list):
        selected = data["clips"]
    elif isinstance(data, dict) and isinstance(data.get("answer"), str):
        answer = data["answer"].strip()
        selected = []
        for i, candidate in enumerate(candidates):
            if answer and answer in candidate["text"]:
                selected.append({"id": i, "title": "AI選出ハイライト", "reason": "Ollamaが候補本文を選択しました。", "score": 70})
                break
    else:
        selected = []

    valid: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for item in selected:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            continue
        cid = int(item["id"])
        if not 0 <= cid < len(candidates) or cid in seen_ids:
            continue
        seen_ids.add(cid)
        item["score"] = max(0, min(100, int(item.get("score", 0))))
        valid.append(item)
    if not valid:
        raise RuntimeError("Ollamaから切り抜き候補を1件も選べませんでした")
    return valid


def _overlaps(start: float, end: float, selected_ranges: list[tuple[float, float]]) -> bool:
    for other_start, other_end in selected_ranges:
        if start < other_end + MIN_CLIP_GAP_SECONDS and end + MIN_CLIP_GAP_SECONDS > other_start:
            return True
    return False


def _select_non_overlapping(selected: list[dict[str, Any]], candidates: list[dict[str, Any]], max_clips: int, duration: float) -> list[dict[str, Any]]:
    ranked = sorted(selected, key=lambda item: (int(item.get("score", 0)), int(candidates[int(item["id"])].get("heuristic", 0))), reverse=True)
    selected_ranges: list[tuple[float, float]] = []
    chosen_ids: set[int] = set()
    result: list[dict[str, Any]] = []

    def try_add(item: dict[str, Any]) -> bool:
        cid = int(item["id"])
        if cid in chosen_ids or not 0 <= cid < len(candidates):
            return False
        c = candidates[cid]
        start = max(0.0, min(float(c["start"]), duration - 1.0))
        end = max(start + 8.0, min(float(c["end"]), duration))
        if _overlaps(start, end, selected_ranges):
            return False
        chosen_ids.add(cid)
        selected_ranges.append((start, end))
        result.append(item)
        return True

    for item in ranked:
        if len(result) >= max_clips:
            break
        try_add(item)

    if len(result) < max_clips:
        fallback = sorted(enumerate(candidates), key=lambda pair: (int(pair[1].get("heuristic", 0)), float(pair[1].get("start", 0.0))), reverse=True)
        for cid, _candidate in fallback:
            if len(result) >= max_clips:
                break
            if cid in chosen_ids:
                continue
            try_add({
                "id": cid,
                "title": f"AI選出ハイライト{len(result) + 1}",
                "reason": "AI選出候補と時間が重ならない別の場面を補充しました。",
                "score": int(candidates[cid].get("heuristic", 0)),
            })
    return result


def create_ai_clips(vod_path: Path, max_clips: int = 3) -> list[Path]:
    segments = transcribe_vod(vod_path)
    if not segments:
        raise RuntimeError("音声から字幕を取得できませんでした")
    candidates = _candidate_windows(segments)
    if not candidates:
        raise RuntimeError("切り抜き候補を作れませんでした")
    selected = _ask_ollama(candidates, max_clips)

    RESULT_DIR.mkdir(exist_ok=True)
    results: list[dict[str, Any]] = []
    outputs: list[Path] = []
    duration = _duration_seconds(vod_path)
    selected = _select_non_overlapping(selected, candidates, max_clips, duration)
    vertical = os.getenv("MEINA_VERTICAL_SHORTS", "0").strip().lower() in {"1", "true", "yes", "on"}

    for index, item in enumerate(selected[:max_clips], 1):
        cid = item["id"]
        c = candidates[cid]
        start = max(0.0, min(c["start"], duration - 1.0))
        end = max(start + 8.0, min(c["end"], duration))
        title = str(item.get("title") or f"切り抜き{index}")
        raw_path = make_clip(vod_path, start, end, title, index)
        path = raw_path
        try:
            path = edit_generated_clip(raw_path, segments, start, end, vertical=vertical)
            print(f"🎬 自動編集完了: {path}")
        except Exception as exc:
            print(f"⚠️ 自動編集をスキップしました: {exc}")
        outputs.append(path)
        results.append({
            "file": str(path),
            "raw_file": str(raw_path),
            "start": start,
            "end": end,
            "title": title,
            "reason": item.get("reason", ""),
            "score": item.get("score", 0),
            "transcript": c["text"],
            "edited": path != raw_path,
            "vertical": vertical,
        })

    (RESULT_DIR / f"{vod_path.stem}.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return outputs


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python twitch_ai_clipper.py twitch_vods/VIDEO.mp4")
    paths = create_ai_clips(Path(sys.argv[1]))
    for path in paths:
        print(f"完成: {path}")
