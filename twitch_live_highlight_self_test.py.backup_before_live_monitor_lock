"""ライブ見どころ候補の依存軽量セルフテスト。"""

from __future__ import annotations

from datetime import datetime, timezone

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

    print("Twitch live highlight self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
