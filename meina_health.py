"""めいなの起動前ヘルスチェック。
実行中のPC状態を変更せず、必須/任意コンポーネントを確認する。
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import sysconfig
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

REQUIRED_EXECUTABLES = (
    "ollama",
    "nvidia-smi",
)

OPTIONAL_EXECUTABLES = (
    "ffmpeg",
    "ffprobe",
)

OLLAMA_MODEL = "meina"
WHISPER_CACHE_DIR_NAME = "models--Systran--faster-whisper-large-v3"


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



def _check_ollama_model() -> tuple[bool, str]:
    path = shutil.which("ollama")
    if not path:
        return False, "ollama: executable not found"
    try:
        result = subprocess.run(
            [path, "list"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        return False, f"ollama: model check failed ({exc})"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip().splitlines()
        message = detail[0] if detail else "unknown error"
        return False, f"ollama: service unavailable ({message})"

    for line in (result.stdout or "").splitlines()[1:]:
        parts = line.split()
        if parts and parts[0].split(":", 1)[0].lower() == OLLAMA_MODEL:
            return True, f"ollama model: {parts[0]}"
    return False, f"ollama model: {OLLAMA_MODEL} not found"


def _cuda_site_packages() -> Path | None:
    active = Path(sysconfig.get_paths().get("purelib", ""))
    candidates = []
    if str(active):
        candidates.append(active)
    candidates.extend(
        (
            ROOT / ".venv_new" / "Lib" / "site-packages",
            ROOT / ".venv" / "Lib" / "site-packages",
        )
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _check_cuda_dlls() -> tuple[bool, str]:
    site_packages = _cuda_site_packages()
    if site_packages is None:
        return False, "CUDA Python site-packages not found"
    cublas = site_packages / "nvidia" / "cublas" / "bin"
    cudnn = site_packages / "nvidia" / "cudnn" / "bin"
    if not cublas.is_dir() or not cudnn.is_dir():
        return False, f"CUDA DLL directories missing: {cublas} / {cudnn}"
    return True, "CUDA DLL directories: OK"



def _check_whisper_cache() -> tuple[str, str]:
    try:
        home = Path.home()
        candidates = [
            home / ".cache" / "huggingface" / "hub" / WHISPER_CACHE_DIR_NAME,
        ]
        hf_home = os.environ.get("HF_HOME")
        if hf_home:
            candidates.insert(0, Path(hf_home) / "hub" / WHISPER_CACHE_DIR_NAME)

        for candidate in candidates:
            if candidate.exists():
                return "OK", f"Whisper large-v3 cache: {candidate}"

        return "WARN", "Whisper large-v3 cache not detected; first startup may download the model"
    except Exception as exc:
        return "WARN", f"Whisper cache check failed ({exc})"


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
    print("Required services:")
    for executable in REQUIRED_EXECUTABLES:
        status, detail = _check_executable(executable)
        print(f"[{status}] {detail}")
        if status != "OK":
            fatal = True

    ollama_ok, ollama_detail = _check_ollama_model()
    ollama_status = "OK" if ollama_ok else "FAIL"
    print(f"[{ollama_status}] {ollama_detail}")
    if not ollama_ok:
        fatal = True

    cuda_ok, cuda_detail = _check_cuda_dlls()
    cuda_status = "OK" if cuda_ok else "FAIL"
    print(f"[{cuda_status}] {cuda_detail}")
    if not cuda_ok:
        fatal = True

    whisper_status, whisper_detail = _check_whisper_cache()
    print()
    print("Whisper model:")
    print(f"[{whisper_status}] {whisper_detail}")

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
    print("   WARNは追加機能や初回ダウンロードなど、起動は可能でも追加処理が必要な項目です。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
