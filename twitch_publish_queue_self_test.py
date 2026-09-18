"""Twitch投稿準備コマンドとキュー生成の軽量セルフテスト。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from command_router import route_command
import twitch_publish_queue as queue


def main() -> int:
    route = route_command("切り抜きの投稿準備して", {"confidence": 0.1})
    assert route is not None
    assert route["kind"] == "twitch_publish_prep"
    assert route["target"] == "latest"
    assert route["confidence"] == 1.0

    original_result = queue.RESULT_DIR
    original_queue = queue.QUEUE_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_dir = root / "results"
            queue_dir = root / "queue"
            result_dir.mkdir()

            video = root / "clip.mp4"
            video.write_bytes(b"test")

            result_file = result_dir / "vod123.json"
            result_file.write_text(
                json.dumps(
                    [{
                        "file": str(video),
                        "title": "クラッチ",
                        "reason": "最後の1v2を取った",
                        "transcript": "クラッチした",
                        "publish": {
                            "title": "1v2クラッチ決めた",
                            "description": "最後の1v2を取り切った場面。",
                            "caption": "まさかの1v2クラッチ",
                            "hashtags": ["#VALORANT", "#切り抜き"],
                            "source": "ollama",
                        },
                    }],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            queue.RESULT_DIR = result_dir
            queue.QUEUE_DIR = queue_dir

            bundle = queue.prepare_publish_queue()
            assert bundle["bundle"]["ready"] is True
            assert bundle["bundle"]["ready_count"] == 1
            assert Path(bundle["json_path"]).exists()
            assert Path(bundle["markdown_path"]).exists()

            markdown = Path(bundle["markdown_path"]).read_text(encoding="utf-8")
            assert "1v2クラッチ決めた" in markdown
            assert "#VALORANT" in markdown
            assert str(video) in markdown
    finally:
        queue.RESULT_DIR = original_result
        queue.QUEUE_DIR = original_queue

    print("Twitch publish queue self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
