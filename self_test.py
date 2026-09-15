"""めいなの軽量セルフテスト。Whisper/Ollamaを起動せず構成を確認する。"""

import command_router
from meina2 import tools


def check(text, expected_kind=None, expected_target=None, expected_query=None):
    frame = {"confidence": 0.95}
    result = command_router.route_command(text, frame)
    if expected_kind is None:
        assert result is None, (text, result)
    else:
        assert result is not None, text
        assert result["kind"] == expected_kind, (text, result)
        if expected_target:
            assert result["target"] == expected_target, (text, result)
        if expected_query is not None:
            assert result["query"] == expected_query, (text, result)
    print("OK:", text, "->", result)


check("メモ帳を開いて", "app_open", "notepad")
check("Discordを開いて", "app_open", "discord")
check("Steamを開いて", "app_open", "steam")
check("OBSを起動して", "app_open", "obs")
check("GoogleでVALORANTについて検索して", "web_search", "google", "valorant")
check("GoogleでVALORANTの最新情報を調べて", "web_search", "google", "valorantの最新情報")
check("YouTubeでVALORANTの動画を検索して", "web_search", "youtube", "valorantの動画")
check("YouTubeでUVERworldの曲を探して", "web_search", "youtube", "uverworldの曲")
check("YouTubeを開いて", "web_open", "youtube")
check("意味不明な命令")

assert command_router.route_command("メモ帳を開いて", {"confidence": 0.69}) is None
print("OK: confidence gate")

for name in (
    "open_notepad", "open_calculator", "open_explorer",
    "launch_app", "open_google", "open_youtube",
    "google_search", "youtube_search",
):
    assert callable(getattr(tools, name, None)), name

print("OK: tools API")
print("\nめいなセルフテスト完了")
