from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_UPGRADE_TWITCH_V1"
IMPORT_LINE = "from meina_twitch_voice import handle_voice_command"


def main() -> None:
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")

    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text or IMPORT_LINE in text:
        print("Meina Twitch upgrade: already applied")
        return

    backup = AGENT.with_name("meina_agent.py.backup_before_twitch")
    if not backup.exists():
        shutil.copy2(AGENT, backup)

    # Importを既存のcommand_router import直後へ追加。
    anchor = "import command_router\n"
    if anchor not in text:
        raise SystemExit("command_router import が見つかりません")
    text = text.replace(anchor, anchor + IMPORT_LINE + "\n", 1)

    # process_commandの先頭でTwitch切り抜き命令を最優先処理する。
    anchor = '''    if is_invalid_command(text):\n'''
    if anchor not in text:
        raise SystemExit("process_command の安全チェック位置が見つかりません")

    block = '''    # MEINA_UPGRADE_TWITCH_V1\n    # Twitch切り抜き命令は通常会話やPC操作より先に処理する。\n    twitch_reply = handle_voice_command(text)\n    if twitch_reply:\n        print("🎬 Twitch:", twitch_reply)\n        speak(twitch_reply)\n        return\n\n'''
    text = text.replace(anchor, block + anchor, 1)

    AGENT.write_text(text, encoding="utf-8")
    print("Meina Twitch upgrade: applied")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
