from __future__ import annotations

import os
import time
from pathlib import Path

from twitch_clip_pipeline import process_latest_vod


INTERVAL = int(os.getenv("MEINA_TWITCH_INTERVAL", "300"))


def main() -> None:
    print("🤖 めいな Twitch自動監視を開始")
    print(f"⏱️ {INTERVAL}秒ごとにVODを確認します")
    while True:
        try:
            vod = process_latest_vod()
            if vod:
                print(f"🎥 新しいVODを検出: {Path(vod).name}")
                print("✂️ 次の段階で、このVODを自動解析して切り抜き化します")
        except KeyboardInterrupt:
            print("\n停止しました")
            return
        except Exception as exc:
            print(f"⚠️ Twitch監視エラー: {exc}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
