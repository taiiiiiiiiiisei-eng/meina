from __future__ import annotations

import os
import time
from pathlib import Path

from twitch_ai_clipper import create_ai_clips
from twitch_clip_pipeline import download_vod, get_latest_vod, load_config, load_state, save_state
from twitch_ffmpeg_env import find_executable

INTERVAL = int(os.getenv("MEINA_TWITCH_INTERVAL", "300"))
MAX_CLIPS = int(os.getenv("MEINA_TWITCH_MAX_CLIPS", "3"))


def configure_ffmpeg() -> None:
    """Make FFmpeg/ffprobe discoverable by child processes on Windows."""
    ffmpeg = Path(find_executable("ffmpeg")).resolve()
    bin_dir = str(ffmpeg.parent)
    current = os.environ.get("PATH", "")
    if bin_dir not in current.split(os.pathsep):
        os.environ["PATH"] = bin_dir + os.pathsep + current


def process_new_vod() -> list[Path] | None:
    """Process only a VOD that has not already been processed successfully."""
    configure_ffmpeg()
    config = load_config()
    vod = get_latest_vod(config)
    if not vod:
        return None

    vod_id = str(vod.get("id", ""))
    state = load_state()
    if vod_id and str(state.get("last_vod_id", "")) == vod_id:
        return None

    vod_path = download_vod(vod)
    if vod_path is None:
        return None

    clips = create_ai_clips(vod_path, max_clips=MAX_CLIPS)
    if vod_id:
        state["last_vod_id"] = vod_id
        save_state(state)
    return clips


def main() -> None:
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
