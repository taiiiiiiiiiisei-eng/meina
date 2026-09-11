import time

from twitch_clipper import TwitchClipper


INTERVAL_SECONDS = 300


def main() -> None:
    clipper = TwitchClipper()
    print("🎥 Twitch自動切り抜き監視を開始しました")
    print(f"⏱️ {INTERVAL_SECONDS // 60}分ごとに新しいVODを確認します")

    while True:
        try:
            result = clipper.process_latest()
            status = result.get("status")

            if status == "completed":
                print("✅ 切り抜き完了:")
                for path in result.get("clips", []):
                    print("  ", path)
            elif status == "already_processed":
                print("⏭️ 最新VODは処理済みです")
            elif status == "no_vod":
                print("ℹ️ VODがまだありません")
            else:
                print("ℹ️ 状態:", status)

        except Exception as exc:
            print("❌ Twitch自動処理エラー:", exc)

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
