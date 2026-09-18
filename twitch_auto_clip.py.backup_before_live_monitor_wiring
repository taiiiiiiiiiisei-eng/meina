from __future__ import annotations

import os
import time

from twitch_auto_clip_v2 import process_new_vod

INTERVAL = int(os.getenv("MEINA_TWITCH_INTERVAL", "300"))


def main() -> None:
    """新しいVODだけを監視し、成功したVODを再処理しない。"""
    print("🤖 めいな Twitch自動切り抜き V2を開始")
    print(f"⏱️ {INTERVAL}秒ごとに新規VODを確認します")

    while True:
        try:
            clips = process_new_vod()
            if clips is None:
                print("⏭️ 新しいVODはありません")
            else:
                for clip in clips:
                    print(f"✅ 切り抜き完成: {clip}")
                if not clips:
                    print("⚠️ AIが切り抜き候補を選べませんでした")
        except KeyboardInterrupt:
            print("\n停止しました")
            return
        except Exception as exc:
            print(f"⚠️ Twitch自動切り抜きエラー: {exc}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
