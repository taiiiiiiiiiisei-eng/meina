"""ライブ見どころ候補の依存軽量セルフテスト。"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import twitch_ai_clipper
import twitch_live_highlight as module


def main() -> int:
    assert module.heuristic_score("") == 0
    assert module.heuristic_score("今日は普通にプレイしています") >= 20
    assert module.heuristic_score("やばい！クラッチした！！！") > module.heuristic_score("今日は普通にプレイしています")

    started = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)
    chunk = datetime(2026, 9, 18, 10, 5, tzinfo=timezone.utc)
    candidate = module.build_candidate(
        chunk,
        started,
        2.5,
        8.0,
        "やばい！クラッチした！",
        {
            "score": 88,
            "title": "クラッチ成功",
            "reason": "強い反応とクラッチを検出",
            "source": "ollama",
        },
    )
    assert candidate["stream_time_start"] == 302.5
    assert candidate["stream_time_end"] == 308.0
    assert candidate["stream_id"] == ""
    assert candidate["score"] == 88

    with_stream = module.build_candidate(
        chunk,
        started,
        1.0,
        4.0,
        "クラッチ！",
        {
            "score": 90,
            "title": "クラッチ",
            "reason": "高評価候補",
            "source": "ollama",
        },
        "stream-123",
    )
    assert with_stream["stream_id"] == "stream-123"
    assert with_stream["stream_time_start"] == 301.0
    assert candidate["source"] == "ollama"

    # VODファイル名と配信stream_idが違っていてもライブ候補を再利用できる。
    original_markers_path = twitch_ai_clipper.LIVE_MARKERS_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp:
            markers_path = Path(tmp) / "candidates.jsonl"
            markers_path.write_text(
                json.dumps(
                    {
                        "stream_id": "stream-123",
                        "stream_time_start": 120.0,
                        "stream_time_end": 130.0,
                        "score": 90,
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            twitch_ai_clipper.LIVE_MARKERS_PATH = markers_path
            matches = twitch_ai_clipper._load_live_markers(
                Path(tmp) / "vod-999.mp4",
                {"stream_id": "stream-123"},
            )
            assert len(matches) == 1
            assert matches[0]["stream_id"] == "stream-123"
    finally:
        twitch_ai_clipper.LIVE_MARKERS_PATH = original_markers_path


    formatted = module.format_candidates([
        {
            "score": 92,
            "stream_time_start": 125.0,
            "title": "クラッチ成功",
            "text": "やばい！クラッチした！",
        }
    ])
    assert "2分5秒" in formatted
    assert "評価92" in formatted
    assert "クラッチ成功" in formatted


    unique = module._deduplicate_candidates([
        {"score": 80, "stream_time_start": 100.0},
        {"score": 95, "stream_time_start": 108.0},
        {"score": 85, "stream_time_start": 140.0},
    ])
    assert [item["stream_time_start"] for item in unique] == [108.0, 140.0]

    fallback = module.format_shortlist(unique[:2])
    assert "おすすめの見どころは2件です。" in fallback
    assert "評価95" in fallback

    original_shortlist_path = module.SHORTLIST_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp:
            shortlist_path = Path(tmp) / "shortlist.json"
            shortlist_path.write_text(
                json.dumps({
                    "shortlist": [
                        {"stream_id": "stream-123", "stream_time_start": 300, "stream_time_end": 310, "score": 95}
                    ]
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            module.SHORTLIST_PATH = shortlist_path
            loaded = module._load_shortlist(Path(tmp) / "vod-999.mp4", {"stream_id": "stream-123"})
            assert len(loaded) == 1
            assert loaded[0]["score"] == 95
    finally:
        module.SHORTLIST_PATH = original_shortlist_path

    print("Twitch live highlight self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
