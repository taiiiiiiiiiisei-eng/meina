"""Twitch切り抜きの投稿準備キューを安全に作成する。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "twitch_clip_results"
QUEUE_DIR = ROOT / "twitch_publish_queue"

def _latest_result_file() -> Path | None:
    if not RESULT_DIR.exists():
        return None
    files = [path for path in RESULT_DIR.glob("*.json") if path.is_file()]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)

def _load_result(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"結果JSONの形式が不正です: {path}")
    return [item for item in data if isinstance(item, dict)]

def prepare_publish_queue(result_path: Path | None = None) -> dict[str, Any]:
    """最新の切り抜き結果から投稿準備用JSON/Markdownを作る。"""
    source = result_path or _latest_result_file()
    if source is None or not source.exists():
        raise FileNotFoundError("投稿準備できる切り抜き結果がありません")

    items = _load_result(source)
    if not items:
        raise ValueError("切り抜き結果が空です")

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    created_at = datetime.now(timezone.utc).isoformat()

    clips: list[dict[str, Any]] = []
    for index, item in enumerate(items, 1):
        publish = item.get("publish") if isinstance(item.get("publish"), dict) else {}
        file_path = Path(str(item.get("file", "")))
        file_exists = bool(str(item.get("file", ""))) and file_path.exists()
        ready = bool(file_exists and publish)
        clips.append({
            "index": index,
            "file": str(file_path),
            "file_exists": file_exists,
            "title": str(publish.get("title") or item.get("title") or f"切り抜き{index}"),
            "description": str(publish.get("description") or item.get("reason") or ""),
            "caption": str(publish.get("caption") or ""),
            "hashtags": [str(x) for x in publish.get("hashtags", []) if str(x).strip()],
            "metadata_source": str(publish.get("source") or "unknown"),
            "ready": ready,
        })

    ready_count = sum(1 for item in clips if item["ready"])
    bundle = {
        "created_at": created_at,
        "source_result": str(source),
        "clip_count": len(clips),
        "ready_count": ready_count,
        "ready": ready_count == len(clips) and len(clips) > 0,
        "clips": clips,
    }

    json_path = QUEUE_DIR / f"{stem}_publish_queue.json"
    md_path = QUEUE_DIR / f"{stem}_publish_queue.md"
    json_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# めいな Twitch投稿準備 — {stem}",
        "",
        f"- 元データ: `{source}`",
        f"- 作成日時(UTC): {created_at}",
        f"- 投稿候補: {len(clips)}本",
        f"- 投稿準備完了: {ready_count}/{len(clips)}本",
        "",
    ]

    for item in clips:
        lines.extend([
            f"## {item['index']}. {item['title']}",
            "",
            f"動画: `{item['file']}`",
            f"動画ファイル存在: {'YES' if item['file_exists'] else 'NO'}",
            "",
            "### キャプション",
            item["caption"],
            "",
            "### 説明",
            item["description"],
            "",
            "### ハッシュタグ",
            " ".join(item["hashtags"]),
            "",
        ])

    lines.extend([
        "---",
        "これは投稿用の下書き・準備データです。",
        "外部SNSへの投稿操作は自動実行しません。",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "ok": True,
        "message": f"Twitch投稿準備を完了しました。{ready_count}/{len(clips)}本が準備済みです。",
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "bundle": bundle,
    }

if __name__ == "__main__":
    result = prepare_publish_queue()
    print(result["message"])
    print(result["markdown_path"])
