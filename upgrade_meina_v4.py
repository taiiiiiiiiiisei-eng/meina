from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_UPGRADE_V4"


def main():
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")

    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Meina upgrade V4: already applied")
        return

    backup = AGENT.with_name("meina_agent.py.backup_before_upgrade_v4")
    if not backup.exists():
        shutil.copy2(AGENT, backup)

    pattern = re.compile(r"def process_command\(text\):\n(    \"\"\".*?\"\"\"\n)", re.S)
    match = pattern.search(text)
    if not match:
        raise SystemExit("process_command が見つかりません")

    replacement = match.group(0) + "\n    global conversation_history\n"
    text = text[:match.start()] + replacement + text[match.end():]
    text = text.replace("# MEINA_UPGRADE_V4", MARKER, 1)
    AGENT.write_text(text, encoding="utf-8")

    print("Meina upgrade V4: applied")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
