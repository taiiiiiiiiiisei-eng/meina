"""めいなの実機向け詳細診断。

本体(meina_agent.py)は起動せず、ローカル環境だけを読み取り確認する。
録音・ファイル削除・プロセス終了などの変更操作は行わない。
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def check_module(name: str) -> tuple[str, str]:
    try:
        return ("OK", name) if importlib.util.find_spec(name) else ("FAIL", f"{name}: missing")
    except Exception as exc:
        return "FAIL", f"{name}: {exc}"


def check_executable(name: str, args: tuple[str, ...] = ("--version",)) -> tuple[str, str]:
    path = shutil.which(name)
    if not path:
        return "WARN", f"{name}: not found"
    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        lines = (result.stdout or result.stderr).splitlines()
        detail = lines[0].strip() if lines else path
        return "OK" if result.returncode == 0 else "WARN", f"{name}: {detail}"
    except Exception as exc:
        return "WARN", f"{name}: {exc}"


def check_ollama() -> tuple[str, str]:
    path = shutil.which("ollama")
    if not path:
        return "WARN", "ollama: executable not found"
    try:
        result = subprocess.run(
            [path, "list"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        return "WARN", f"ollama: {exc}"

    output = (result.stdout or "").strip()
    if result.returncode != 0:
        return "WARN", "ollama: command exists but local service is unavailable"
    has_meina = "meina" in output.lower()
    return (
        "OK" if has_meina else "WARN",
        "ollama: service OK; meina model found" if has_meina else "ollama: service OK; meina model not listed",
    )


def check_microphone() -> tuple[str, str]:
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        inputs = [d for d in devices if int(d.get("max_input_channels", 0)) > 0]
        if not inputs:
            return "WARN", "microphone: no input device found"
        names = ", ".join(str(d.get("name", "unknown")) for d in inputs[:3])
        extra = "" if len(inputs) <= 3 else f" (+{len(inputs) - 3})"
        return "OK", f"microphone: {names}{extra}"
    except Exception as exc:
        return "WARN", f"microphone: {exc}"


def check_tts() -> tuple[str, str]:
    try:
        import pyttsx3

        engine = pyttsx3.init()
        voices = engine.getProperty("voices") or []
        names = []
        for voice in voices[:5]:
            name = getattr(voice, "name", None) or getattr(voice, "id", None)
            if name:
                names.append(str(name))
        engine.stop()
        if not voices:
            return "WARN", "Windows TTS: no voices reported"
        return "OK", "Windows TTS: " + ", ".join(names)
    except Exception as exc:
        return "WARN", f"Windows TTS: {exc}"


def check_cuda() -> tuple[str, str]:
    try:
        import site

        candidates = []
        candidates.extend(site.getsitepackages())
        user_site = site.getusersitepackages()
        if user_site:
            candidates.append(user_site)
        prefix = Path(sys.prefix)
        candidates.extend(
            [
                str(prefix / "Lib" / "site-packages"),
                str(Path(sys.executable).resolve().parent / "Lib" / "site-packages"),
            ]
        )

        found = []
        for base in candidates:
            for package in ("cublas", "cudnn"):
                path = Path(base) / "nvidia" / package / "bin"
                if path.is_dir():
                    found.append(f"{package}={path}")
        if not found:
            return "WARN", "CUDA DLL directories not found"
        return "OK", "CUDA DLLs: " + " | ".join(found[:4])
    except Exception as exc:
        return "WARN", f"CUDA: {exc}"


def _cache_candidates() -> list[Path]:
    home = Path.home()
    candidates = [
        home / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-large-v3",
        home / ".cache" / "huggingface" / "hub",
        home / ".cache" / "huggingface",
    ]
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        candidates.insert(0, Path(hf_home))
    return candidates


def check_whisper_cache() -> tuple[str, str]:
    try:
        candidates = _cache_candidates()
        exact = candidates[0]
        if exact.exists():
            return "OK", f"Whisper large-v3 cache: {exact}"
        for root in candidates[1:]:
            if root.exists() and "faster-whisper-large-v3" in root.name.lower():
                return "OK", f"Whisper cache: {root}"
        return "WARN", "Whisper large-v3 cache not detected in standard locations"
    except Exception as exc:
        return "WARN", f"Whisper cache: {exc}"


def main() -> int:
    print("=" * 76)
    print("🤖 めいな 実機ドクター")
    print("=" * 76)
    print(f"Python : {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    print(f"Project: {ROOT}")
    print()

    checks: list[tuple[str, str, str]] = []

    if sys.version_info >= (3, 12):
        checks.append(("Python", "OK", "3.12+"))
    else:
        checks.append(("Python", "FAIL", "3.12+ required"))

    for module in ("sounddevice", "pyttsx3", "ollama", "faster_whisper"):
        status, detail = check_module(module)
        checks.append(("Package", status, detail))

    for executable in ("nvidia-smi", "ffmpeg", "ffprobe", "yt-dlp"):
        status, detail = check_executable(executable)
        checks.append(("Executable", status, detail))

    for label, checker in (
        ("Ollama", check_ollama),
        ("Microphone", check_microphone),
        ("Windows TTS", check_tts),
        ("CUDA", check_cuda),
        ("Whisper", check_whisper_cache),
    ):
        status, detail = checker()
        checks.append((label, status, detail))

    required_files = (
        "meina_agent.py",
        "meina_app.py",
        "command_router.py",
        "run_meina.py",
        "meina_brain/brain_core.py",
        "meina2/tools.py",
    )
    missing = [name for name in required_files if not (ROOT / name).exists()]
    checks.append(
        ("Files", "OK" if not missing else "FAIL",
         "all core files present" if not missing else "missing: " + ", ".join(missing))
    )

    for category, status, detail in checks:
        print(f"[{status:4}] {category:12} {detail}")

    print()
    failures = sum(status == "FAIL" for _, status, _ in checks)
    warnings = sum(status == "WARN" for _, status, _ in checks)
    if failures:
        print(f"❌ Doctor result: FAIL ({failures} failure(s), {warnings} warning(s))")
        print("   FAIL項目を先に直してください。")
        return 1

    print(f"✅ Doctor result: READY ({warnings} warning(s))")
    if warnings:
        print("   WARNは追加機能または環境依存項目です。本体起動を必ずしも妨げません。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
