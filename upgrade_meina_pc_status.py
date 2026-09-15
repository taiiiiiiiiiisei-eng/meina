from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_UPGRADE_PC_STATUS_V1"
IMPORT_LINE = "from meina_pc_status import get_pc_status, format_pc_status"


def main() -> None:
    if not AGENT.exists():
        raise SystemExit("meina_agent.py が見つかりません")

    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text or IMPORT_LINE in text:
        print("Meina PC status upgrade: already applied")
        return

    backup = AGENT.with_name("meina_agent.py.backup_before_pc_status")
    if not backup.exists():
        shutil.copy2(AGENT, backup)

    anchor = "import command_router\n"
    if anchor not in text:
        raise SystemExit("command_router import が見つかりません")
    text = text.replace(anchor, anchor + IMPORT_LINE + "\n", 1)

    anchor = '''    query = route["query"]\n'''
    if anchor not in text:
        raise SystemExit("execute_routed_command のquery位置が見つかりません")

    block = '''    # MEINA_UPGRADE_PC_STATUS_V1\n    if kind == "pc_status":\n        try:\n            result = format_pc_status(get_pc_status())\n            print("🖥️ PC状態:", result)\n            speak(result)\n            return True\n        except Exception as e:\n            print("❌ PC状態取得エラー:", e)\n            speak("PCの状態を取得できませんでした")\n            return True\n\n'''
    text = text.replace(anchor, anchor + "\n" + block, 1)

    AGENT.write_text(text, encoding="utf-8")
    print("Meina PC status upgrade: applied")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
