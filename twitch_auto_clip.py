from __future__ import annotations

import os
import time
from pathlib import Path

from twitch_ai_clipper import create_ai_clips
from twitch_clip_pipeline import process_latest_vod

INTERVAL = int(os.getenv("MEINA_TWITCH_INTERVAL", "300"))
MAX_CLIPS = int(os.getenv("MEINA_TWITCH_MAX_CLIPS", "3"))


def main() -> None:
    print("🤖 めいな Twitch自動切り抜きを開始")
    print(f"⏱️ {INTERVAL}秒ごとにVODを確認します")
    while True:
        try:
            vod = process_latest_vod()
            if vod:
                print(f"🎥 新しいVOD: {Path(vod).name}")
                print("🧠 Whisperで文字起こし → Ollamaで見どころ判定 → FFmpegで切り抜き")
                clips = create_ai_clips(vod, max_clips=MAX_CLIPS)
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
