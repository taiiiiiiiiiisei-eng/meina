from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_UPGRADE_V2"


def main():
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")

    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Meina upgrade: already applied")
        return

    backup = AGENT.with_name("meina_agent.py.backup_before_upgrade_v2")
    if not backup.exists():
        shutil.copy2(AGENT, backup)

    if "import json\n" not in text:
        text = text.replace("import os\n", "import os\nimport json\n", 1)
    if "from datetime import datetime\n" not in text:
        text = text.replace("import json\n", "import json\nfrom datetime import datetime\n", 1)

    old = '''        ("メイナー", "メイナ"),\n        ("めいナー", "めいな"),'''
    new = '''        ("ばろらんとと", "バロラント"),\n        ("バロラントト", "バロラント"),\n        ("バロラントー", "バロラント"),\n        ("ばろらんと", "バロラント"),\n        ("メイナー", "メイナ"),\n        ("めいナー", "めいな"),'''
    if old in text and "ばろらんとと" not in text:
        text = text.replace(old, new, 1)

    memory_block = r'''# MEINA_UPGRADE_V2
# =========================================================
# 会話メモリ / 自然な会話
# =========================================================

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "meina_memory.json")
MAX_HISTORY = 16
MAX_MEMORY_CHARS = 6000


def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data[-MAX_HISTORY:]
    except Exception as e:
        print("⚠️ メモリ読み込みエラー:", e)
    return []


def save_memory(history):
    try:
        history = history[-MAX_HISTORY:]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠️ メモリ保存エラー:", e)


conversation_history = load_memory()


def _trim_history(history):
    """会話履歴が大きくなりすぎないよう制限する。"""
    result = []
    total = 0
    for item in reversed(history[-MAX_HISTORY:]):
        content = str(item.get("content", ""))
        total += len(content)
        if total > MAX_MEMORY_CHARS:
            break
        result.append(item)
    result.reverse()
    return result


def answer_datetime(text):
    """現在の日付・時刻をPCのローカル時刻から正確に返す。"""
    value = normalize_text(text)
    now = datetime.now()
    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

    time_phrases = ("今何時", "いま何時", "現在何時", "今の時間", "現在の時間", "現在時刻", "今何時ですか")
    date_phrases = ("今日の日付", "今日は何日", "何月何日", "現在の日付")

    if any(key in value for key in time_phrases) or value in ("何時", "時間", "時刻"):
        return f"現在は{now.hour}時{now.minute}分です。"
    if any(key in value for key in date_phrases) or value == "日付":
        return f"今日は{now.year}年{now.month}月{now.day}日です。"
    if "何曜日" in value or value == "曜日":
        return f"今日は{weekdays[now.weekday()]}です。"
    return None


'''
    ollama_marker = "# =========================================================\n# Ollama会話\n# =========================================================\n"
    if ollama_marker not in text:
        raise SystemExit("Ollama会話セクションが見つかりません")
    text = text.replace(ollama_marker, memory_block + ollama_marker, 1)

    chat_pattern = re.compile(
        r"def chat_with_meina\(text\):.*?(?=\n\n# =========================================================\n# 命令処理)",
        re.S,
    )
    chat_function = '''def chat_with_meina(text):
    """普通の会話をOllamaへ送り、直近の会話を文脈として維持する。"""

    if not text:
        return ""

    global conversation_history

    try:
        history = _trim_history(conversation_history)

        system_prompt = (
            "あなたはローカル音声AIアシスタント『めいな』です。"
            "日本語で自然に会話してください。"
            "ユーザーの発言に直接答え、短く自然な返答を優先してください。"
            "雑談では堅苦しくならず、会話が続くように返してください。"
            "PC操作を要求された場合は、別の安全な操作ルートが処理するため、"
            "ここでは勝手にコマンドやシェル操作を提案しないでください。"
        )

        messages = [
            {"role": "system", "content": system_prompt}
        ] + history + [
            {"role": "user", "content": text}
        ]

        response = ollama.chat(
            model="meina",
            messages=messages
        )

        answer = response["message"]["content"].strip()
        if not answer:
            answer = "すみません、うまく答えられませんでした。"

        conversation_history.extend([
            {"role": "user", "content": text},
            {"role": "assistant", "content": answer},
        ])
        conversation_history = _trim_history(conversation_history)
        save_memory(conversation_history)

        print("🧠 めいな:", answer)
        speak(answer)
        return answer

    except Exception as e:
        print("❌ Ollamaエラー:", e)
        speak("すみません、うまく答えられませんでした")
        return ""
'''
    if not chat_pattern.search(text):
        raise SystemExit("chat_with_meina が見つかりません")
    text = chat_pattern.sub(chat_function, text, count=1)

    process_marker = '''    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")\n\n    # =====================================================\n    # brain_core\n    # =====================================================\n'''
    process_replacement = '''    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")\n\n    # =====================================================\n    # 正確な日付・時刻\n    # =====================================================\n\n    datetime_answer = answer_datetime(text)\n    if datetime_answer:\n        print("🕒", datetime_answer)\n        speak(datetime_answer)\n        return\n\n    # =====================================================\n    # brain_core\n    # =====================================================\n'''
    if process_marker not in text:
        raise SystemExit("process_command の挿入位置が見つかりません")
    text = text.replace(process_marker, process_replacement, 1)

    AGENT.write_text(text, encoding="utf-8")
    print("Meina upgrade: applied V2")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
