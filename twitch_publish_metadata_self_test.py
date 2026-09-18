"""投稿メタデータ生成の依存軽量テスト。"""

from __future__ import annotations

import twitch_publish_metadata as module


def main() -> int:
    original = module.requests
    try:
        module.requests = None
        result = module.generate_publish_metadata([
            {
                "title": "クラッチ成功",
                "reason": "最後の1v2を取り切った場面",
                "transcript": "これは絶対無理だと思ったけどクラッチした",
            }
        ])
    finally:
        module.requests = original

    assert len(result) == 1
    item = result[0]
    assert item["source"] == "fallback"
    assert item["title"]
    assert item["description"]
    assert item["caption"]
    assert isinstance(item["hashtags"], list)
    assert "#Twitch" in item["hashtags"]

    print("Twitch publish metadata self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
