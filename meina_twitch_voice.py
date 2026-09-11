from __future__ import annotations

from meina_twitch import is_twitch_clip_request, run_twitch_clip_command


def handle_voice_command(text: str) -> str | None:
    """Return a spoken result when text is a Twitch clipping command."""
    if not is_twitch_clip_request(text):
        return None
    result = run_twitch_clip_command(text)
    if not result.get("ok"):
        return "Twitchの切り抜き命令として処理できませんでした。"
    clips = result.get("clips", [])
    return f"切り抜きを{len(clips)}本作りました。clipsフォルダに保存しました。"
