"""めいなのローカル記憶を本体へ安全に接続する起動時アップグレード。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_MEMORY_INTEGRATION_V1"


def patch_agent() -> bool:
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("meina_agent.py: memory integration already applied")
        return False

    backup = ROOT / "meina_agent.py.backup_before_memory_integration_v1"
    if not backup.exists():
        backup.write_text(text, encoding="utf-8")
        print(f"Backup created: {backup}")

    old_import = "import command_router\n"
    new_import = old_import + "\nfrom meina_memory import (\n    add_conversation,\n    add_task,\n    get_user_setting,\n    list_tasks,\n    remember_fact,\n    recall_fact,\n    set_user_setting,\n)\n"
    if old_import not in text:
        raise RuntimeError("command_router import anchor not found")
    text = text.replace(old_import, new_import, 1)

    anchor = "# =========================================================\n# 命令処理\n# =========================================================\n"
    helpers = '''# MEINA_MEMORY_INTEGRATION_V1\n# =========================================================\n# ローカル記憶・秘書コマンド\n# =========================================================\n\n_MEMORY_BLOCKED_WORDS = ("パスワード", "認証コード", "APIキー", "秘密鍵", "シークレット")\n\ndef handle_memory_command(text):\n    value = normalize_text(text)\n    if not value:\n        return False\n\n    if value.startswith("覚えて") or value.startswith("記憶して"):\n        payload = value.replace("覚えて", "", 1).replace("記憶して", "", 1).strip(" 、:：")\n        if not payload:\n            speak("何を覚えればいいですか？")\n            return True\n        if any(word in payload for word in _MEMORY_BLOCKED_WORDS):\n            speak("安全のため、パスワードや認証情報は記憶しません")\n            return True\n        remember_fact("latest", payload)\n        speak("覚えました")\n        return True\n\n    if value in ("何を覚えてる", "何を覚えてる？", "覚えてること", "記憶を教えて"):\n        fact = recall_fact("latest")\n        if fact:\n            speak("覚えていることは、" + str(fact))\n        else:\n            speak("まだ記憶していることはありません")\n        return True\n\n    if value in ("今日やること", "今日やることは", "今日の予定"):\n        tasks = list_tasks()\n        pending = [item.get("text", "") for item in tasks if not item.get("done")]\n        if pending:\n            speak("今日やることは、" + "、".join(pending[:5]))\n        else:\n            speak("今日やることはまだ登録されていません")\n        return True\n\n    if value.startswith("今日やること") and len(value) > 6:\n        payload = value[len("今日やること"):].strip(" 、:：")\n        if payload:\n            add_task(payload)\n            speak("今日やることに追加しました")\n            return True\n\n    return False\n\n\n'''
    if anchor not in text:
        raise RuntimeError("process command anchor not found")
    text = text.replace(anchor, helpers + anchor, 1)

    old_process = "    print(\"\")\n    print(\"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\")\n    print(\n        \"📝 命令:\",\n        text\n    )\n"
    new_process = "    if handle_memory_command(text):\n        return\n\n    add_conversation(\"user\", text)\n\n    print(\"\")\n    print(\"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\")\n    print(\n        \"📝 命令:\",\n        text\n    )\n"
    if old_process not in text:
        raise RuntimeError("process command logging anchor not found")
    text = text.replace(old_process, new_process, 1)

    old_chat = "        speak(\n            answer\n        )\n\n        return answer\n"
    new_chat = "        add_conversation(\"assistant\", answer)\n\n        speak(\n            answer\n        )\n\n        return answer\n"
    if old_chat not in text:
        raise RuntimeError("chat answer anchor not found")
    text = text.replace(old_chat, new_chat, 1)

    AGENT.write_text(text, encoding="utf-8")
    print("meina_agent.py: memory integration applied")
    return True


if __name__ == "__main__":
    patch_agent()
