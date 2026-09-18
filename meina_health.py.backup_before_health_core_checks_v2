"""めいなの起動前ヘルスチェック。
実行中のPC状態を変更せず、必須/任意コンポーネントを確認する。
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = (
    "meina_agent.py",
    "command_router.py",
    "meina_app.py",
    "run_meina.py",
    "meina_brain/brain_core.py",
    "meina2/tools.py",
)

REQUIRED_MODULES = (
    "sounddevice",
    "pyttsx3",
    "ollama",
    "faster_whisper",
)

OPTIONAL_EXECUTABLES = (
    "ollama",
    "ffmpeg",
    "ffprobe",
    "nvidia-smi",
)


def _version_ok() -> bool:
    return sys.version_info >= (3, 12)


def _check_files() -> tuple[bool, list[str]]:
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).exists()]
    return not missing, missing


def _check_modules() -> tuple[bool, list[str]]:
    missing = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
    return not missing, missing


def _check_executable(name: str) -> tuple[str, str]:
    path = shutil.which(name)
    if not path:
        return "WARN", f"{name}: not found"
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        line = (result.stdout or result.stderr).splitlines()
        detail = line[0].strip() if line else path
        return "OK", f"{name}: {detail}"
    except Exception as exc:
        return "WARN", f"{name}: found, version check failed ({exc})"


def main() -> int:
    print("=" * 68)
    print("🤖 めいな 起動前ヘルスチェック")
    print("=" * 68)
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    print()

    fatal = False

    if _version_ok():
        print("[OK] Python version")
    else:
        print("[FAIL] Python 3.12+ is required")
        fatal = True

    files_ok, missing_files = _check_files()
    if files_ok:
        print("[OK] Required project files")
    else:
        print("[FAIL] Missing files:")
        for name in missing_files:
            print(f"       - {name}")
        fatal = True

    modules_ok, missing_modules = _check_modules()
    if modules_ok:
        print("[OK] Required Python packages")
    else:
        print("[FAIL] Missing Python packages:")
        for name in missing_modules:
            print(f"       - {name}")
        fatal = True

    print()
    print("Optional components:")
    for executable in OPTIONAL_EXECUTABLES:
        status, detail = _check_executable(executable)
        print(f"[{status}] {detail}")

    print()
    if fatal:
        print("❌ 必須環境に問題があります。上のFAIL項目を直してから起動してください。")
        return 1

    print("✅ めいなの起動に必要な基本環境はOKです。")
    print("   WARNは追加機能（Twitch/FFmpeg/NVIDIA/Ollamaサービス等）に関するものです。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
