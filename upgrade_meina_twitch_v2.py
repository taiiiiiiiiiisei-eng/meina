from __future__ import annotations

from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_UPGRADE_TWITCH_V2"
IMPORT_LINE = "from meina_twitch_voice import handle_voice_command"


def main() -> None:
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Meina Twitch V2: already applied")
        return
    backup = AGENT.with_name("meina_agent.py.backup_before_twitch_v2")
    if not backup.exists():
        shutil.copy2(AGENT, backup)
    if IMPORT_LINE not in text:
        match = re.search(r"^import command_router\s*$", text, re.MULTILINE)
        if not match:
            raise SystemExit("command_router import が見つかりません")
        text = text[:match.end()] + "\n" + IMPORT_LINE + text[match.end():]
    if "def process_command(text):" not in text:
        raise SystemExit("process_command が見つかりません")
    if "twitch_reply = handle_voice_command(text)" not in text:
        anchor = re.search(r"^    if is_invalid_command\(text\):\s*$", text, re.MULTILINE)
        if not anchor:
            raise SystemExit("process_command の安全チェック位置が見つかりません")
        block = ("    " + MARKER + "\n"
                 "    # Twitch切り抜き命令を通常会話・PC操作より先に処理する。\n"
                 "    twitch_reply = handle_voice_command(text)\n"
                 "    if twitch_reply:\n"
                 "        print(\"🎬 Twitch:\", twitch_reply)\n"
                 "        speak(twitch_reply)\n"
                 "        return\n\n")
        text = text[:anchor.start()] + block + text[anchor.start():]
    AGENT.write_text(text, encoding="utf-8")
    print("Meina Twitch V2: applied")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
