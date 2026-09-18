"""切り抜き動画の投稿用メタデータをローカルAIで生成する。"""

from __future__ import annotations

import json
import os
import re
from typing import Any

try:
    import requests
except ImportError:
    requests = None


OLLAMA_URL = os.getenv("MEINA_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("MEINA_OLLAMA_MODEL", "meina")


def _fallback(item: dict[str, Any], index: int) -> dict[str, Any]:
    title = str(item.get("title") or f"神プレイ切り抜き{index}")
    transcript = str(item.get("transcript") or "").strip()
    base = re.sub(r"\s+", " ", transcript)[:70]
    game_text = " ".join([
        str(item.get("title") or ""),
        str(item.get("reason") or ""),
        transcript,
    ]).lower()
    if any(word in game_text for word in ("apex", "エーペックス", "エペ")):
        game_tag = "#ApexLegends"
    elif any(word in game_text for word in ("valorant", "valo", "バロ", "ヴァロ")):
        game_tag = "#VALORANT"
    else:
        game_tag = "#ゲーム実況"
    hashtags = [game_tag, "#ゲーム実況", "#切り抜き", "#Twitch"]
    return {
        "title": title[:60],
        "description": str(item.get("reason") or "配信から自動選出したハイライトです。"),
        "caption": (title + ("｜" + base if base else ""))[:110],
        "hashtags": hashtags,
        "source": "fallback",
    }


def _parse_payload(content: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []

    if isinstance(data, dict) and isinstance(data.get("clips"), list):
        data = data["clips"]
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def generate_publish_metadata(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """複数切り抜きの投稿文を1回のOllama呼び出しで生成する。"""
    if not items:
        return []

    if requests is None:
        return [_fallback(item, i) for i, item in enumerate(items, 1)]

    payload_items = []
    for i, item in enumerate(items, 1):
        payload_items.append({
            "id": i,
            "title": str(item.get("title") or ""),
            "reason": str(item.get("reason") or ""),
            "transcript": str(item.get("transcript") or "")[:1000],
        })

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
                        "description": {"type": "string"},
                        "caption": {"type": "string"},
                        "hashtags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 6,
                        },
                    },
                    "required": ["id", "title", "description", "caption", "hashtags"],
                },
            }
        },
        "required": ["clips"],
    }

    prompt = (
        "日本語ゲーム配信の切り抜き動画をSNSへ投稿するための文章を作成してください。"
        "誇張しすぎず、候補本文から読み取れる内容だけを使ってください。"
        "タイトルは60文字以内、キャプションは110文字以内、ハッシュタグは最大6個。"
        "VALORANTの場合は#VALORANTを優先してください。必ずJSONだけを返してください。\n"
        + json.dumps(payload_items, ensure_ascii=False)
    )

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "format": schema,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"temperature": 0.4},
            },
            timeout=90,
        )
        response.raise_for_status()
        generated = _parse_payload(response.json().get("message", {}).get("content", ""))
    except Exception as exc:
        print(f"⚠️ 投稿メタデータ生成をフォールバックします: {exc}")
        generated = []

    by_id = {
        int(item.get("id")): item
        for item in generated
        if isinstance(item.get("id"), int)
    }

    result = []
    for i, item in enumerate(items, 1):
        value = by_id.get(i)
        if not value:
            result.append(_fallback(item, i))
            continue

        hashtags = [
            str(tag).strip()
            for tag in value.get("hashtags", [])
            if str(tag).strip()
        ][:6]
        result.append({
            "title": str(value.get("title") or item.get("title") or f"切り抜き{i}")[:60],
            "description": str(value.get("description") or item.get("reason") or "")[:300],
            "caption": str(value.get("caption") or value.get("title") or "")[:110],
            "hashtags": hashtags,
            "source": "ollama",
        })

    return result
