from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_UPGRADE_V3"


def main():
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")

    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Meina upgrade V3: already applied")
        return

    backup = AGENT.with_name("meina_agent.py.backup_before_upgrade_v3")
    if not backup.exists():
        shutil.copy2(AGENT, backup)

    # ---------------------------------------------------------
    # 1. Whisper固有名詞補正を強化
    # ---------------------------------------------------------
    anchor = '    corrections = [\n'
    if anchor not in text:
        raise SystemExit("correct_recognition の corrections が見つかりません")

    additions = '''    corrections = [\n        ("バロラントト", "バロラント"),\n        ("ばろらんとと", "バロラント"),\n        ("バロラントー", "バロラント"),\n        ("ばろらんとー", "バロラント"),\n        ("バロラン", "バロラント"),\n        ("ばろらん", "バロラント"),\n        ("バルラン", "バロラント"),\n        ("ばるらん", "バロラント"),\n        ("バルラント", "バロラント"),\n        ("ばるらんと", "バロラント"),\n'''
    text = text.replace(anchor, additions, 1)

    # 元のリストにある重複項目は動作上問題ないのでそのまま残す。

    # ---------------------------------------------------------
    # 2. 「さっき何言った？」を決定論的に処理
    # ---------------------------------------------------------
    recall_block = r'''# MEINA_UPGRADE_V3
# =========================================================
# 会話リコール / 自然会話強化
# =========================================================


def recall_from_history(text):
    """直前のユーザー発言を履歴から確実に返す。LLMに推測させない。"""
    value = normalize_text(text)
    recall_keys = (
        "俺なんて言ってた",
        "私なんて言ってた",
        "何言ってた",
        "何を言ってた",
        "さっき何言った",
        "さっき何を言った",
        "さっきの話",
        "一個前",
        "一つ前",
        "直前の話",
        "前の話",
        "何話してた",
        "何を話してた",
        "覚えてる",
    )
    if not any(key in value for key in recall_keys):
        return None

    users = [
        item.get("content", "").strip()
        for item in conversation_history
        if item.get("role") == "user" and item.get("content", "").strip()
    ]

    if not users:
        return "まだ会話履歴がありません。"

    # 現在の質問自身はまだ履歴に入っていないので、最後のuser発言が直前発言。
    last = users[-1]
    return f"さっき言っていたのは「{last}」です。"


def clean_chat_answer(text):
    """音声アシスタント向けに明らかな不自然さを軽く除去する。"""
    if not text:
        return ""
    result = text.strip()
    result = result.replace("exhaustion", "")
    result = result.replace("バラエティで取り組んでいる", "どんなところで遊んでいる")
    result = result.replace("いてもらしくね", "で疲れたんだね")
    return result.strip()

'''
    # Insert before the existing Ollama section, after V2 memory functions.
    ollama_marker = "# =========================================================\n# Ollama会話\n# =========================================================\n"
    if ollama_marker not in text:
        raise SystemExit("Ollama会話セクションが見つかりません")
    if "def recall_from_history(text):" not in text:
        text = text.replace(ollama_marker, recall_block + ollama_marker, 1)

    # ---------------------------------------------------------
    # 3. chat_with_meina を自然な日本語向けに強化
    # ---------------------------------------------------------
    chat_pattern = re.compile(
        r"def chat_with_meina\(text\):.*?(?=\n\n# =========================================================\n# 命令処理)",
        re.S,
    )
    chat_function = '''def chat_with_meina(text):
    """普通の会話をOllamaへ送り、自然な日本語と直近履歴を維持する。"""

    if not text:
        return ""

    global conversation_history

    try:
        history = _trim_history(conversation_history)

        system_prompt = (
            "あなたは日本語のローカル音声AIアシスタント『めいな』です。"
            "友達と話すような自然で親しみやすい日本語で答えてください。"
            "ユーザーの発言を勝手に別の意味へ変えないでください。"
            "知らないことは推測せず、わからないときは短く確認してください。"
            "英単語や不自然な言い換えを勝手に混ぜないでください。"
            "ユーザーが疲れた、嬉しい、悲しいなどの気持ちを話したら、"
            "まず自然に受け止めてから、必要なら一つだけ話題を広げてください。"
            "返答は基本的に1〜3文程度の短い日本語にしてください。"
            "PC操作については安全な操作ルートが別に処理するので、"
            "ここではシェルコマンドや危険な操作を提案しないでください。"
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
        answer = clean_chat_answer(answer)
        if not answer:
            answer = "ごめん、うまく答えられなかった。"

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
        speak("ごめん、うまく答えられなかった")
        return ""
'''
    match = chat_pattern.search(text)
    if not match:
        raise SystemExit("chat_with_meina が見つかりません")
    text = chat_pattern.sub(chat_function, text, count=1)

    # ---------------------------------------------------------
    # 4. process_command の最初にリコール処理を追加
    # ---------------------------------------------------------
    process_anchor = '''    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")\n\n    # =====================================================\n    # 正確な日付・時刻\n    # =====================================================\n'''
    process_replacement = '''    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")\n\n    # =====================================================\n    # 会話リコール（LLMに推測させない）\n    # =====================================================\n\n    recall_answer = recall_from_history(text)\n    if recall_answer:\n        print("🧠 会話リコール:", recall_answer)\n        # リコール質問そのものも履歴に残す\n        conversation_history.extend([\n            {"role": "user", "content": text},\n            {"role": "assistant", "content": recall_answer},\n        ])\n        conversation_history = _trim_history(conversation_history)\n        save_memory(conversation_history)\n        speak(recall_answer)\n        return\n\n    # =====================================================\n    # 正確な日付・時刻\n    # =====================================================\n'''
    if process_anchor not in text:
        raise SystemExit("process_command の日付処理位置が見つかりません")
    text = text.replace(process_anchor, process_replacement, 1)

    AGENT.write_text(text, encoding="utf-8")
    print("Meina upgrade V3: applied")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
