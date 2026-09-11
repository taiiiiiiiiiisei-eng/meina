import json
import ollama

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


SYSTEM_PROMPT = """
あなたはWindows PCアシスタント「めいな」です。

ユーザーの日本語を理解して、最適なactionを1つ選んでください。

必ずJSONだけを返してください。

使用できるaction：

date
time
weekday
notepad
calculator
explorer
google
youtube
google_search
youtube_search
launch_app
remember
memory_search
memory_clear
chat

JSON形式：

{
  "action": "アクション名",
  "query": "必要な内容"
}

ルール：

「今日は何日？」
→ date

「今何時？」
→ time

「今日何曜日？」
→ weekday

「メモ帳を開いて」
→ notepad

「電卓を開いて」
→ calculator

「エクスプローラーを開いて」
→ explorer

「Googleを開いて」
→ google

「YouTubeを開いて」
→ youtube

「○○をGoogleで検索して」
→ google_search

「YouTubeで○○を検索して」
→ youtube_search

「Discordを開いて」
→ launch_app
queryはDiscord

「Steamを開いて」
→ launch_app
queryはSteam

「Chromeを開いて」
→ launch_app
queryはChrome

「○○を覚えて」
→ remember

「前に覚えた○○について教えて」
→ memory_search

「覚えていることを全部消して」
→ memory_clear

それ以外の普通の会話
→ chat
"""


def decide(command):

    # ==========================================
    # まずPCアプリ操作を判定
    # ==========================================

    text = (
        command
        .lower()
        .replace(" ", "")
        .replace("　", "")
        .replace("。", "")
        .replace("！", "")
        .replace("!", "")
    )

    apps = {
        "ディスコード": "Discord",
        "discord": "Discord",
        "スチーム": "Steam",
        "steam": "Steam",
        "クローム": "Chrome",
        "chrome": "Chrome",
        "エッジ": "Edge",
        "edge": "Edge",
    }

    open_words = [
        "開いて",
        "開けて",
        "起動して",
        "起動",
        "立ち上げて",
        "立ち上げる",
        "立ち上げ",
    ]

    for word, app_name in apps.items():

        if word in text:

            if any(
                w in text
                for w in open_words
            ):

                return {
                    "action": "launch_app",
                    "query": app_name,
                    "command": command
                }


    # ==========================================
    # Ollamaに判断させる
    # ==========================================

    try:

        response = ollama.chat(
            model=config["ollama_model"],
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": command
                }
            ],
            format="json"
        )

        result = json.loads(
            response["message"]["content"]
        )

        if not isinstance(result, dict):
            raise ValueError(
                "AIの返答がJSONではありません"
            )

        action = result.get(
            "action",
            "chat"
        )

        query = result.get(
            "query",
            ""
        )

        allowed_actions = [
            "date",
            "time",
            "weekday",
            "notepad",
            "calculator",
            "explorer",
            "google",
            "youtube",
            "google_search",
            "youtube_search",
            "launch_app",
            "remember",
            "memory_search",
            "memory_clear",
            "chat"
        ]

        if action not in allowed_actions:
            action = "chat"

        return {
            "action": action,
            "query": str(query),
            "command": command
        }

    except Exception as e:

        print()
        print(
            "❌ AI判断エラー：",
            e
        )

        return {
            "action": "chat",
            "query": command,
            "command": command
        }