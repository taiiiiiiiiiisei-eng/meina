from __future__ import annotations

import os
import time

from twitch_auto_clip_v2 import process_new_vod
from twitch_live_monitor import run_live_monitor

INTERVAL = max(10, int(os.getenv("MEINA_TWITCH_INTERVAL", "300")))
MODE = os.getenv("MEINA_TWITCH_MONITOR_MODE", "live").strip().lower()


def run_vod_monitor() -> None:
    """従来の新規VOD監視を互換用として残す。"""
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


def main() -> None:
    if MODE == "vod":
        run_vod_monitor()
        return
    run_live_monitor()


if __name__ == "__main__":
    main()
