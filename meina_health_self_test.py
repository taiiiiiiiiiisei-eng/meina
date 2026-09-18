"""起動前ヘルスチェックの軽量セルフテスト。"""

from __future__ import annotations

import subprocess
from pathlib import Path

import meina_health


ROOT = Path(__file__).resolve().parent


class _Output:
    def splitlines(self):
        return ["NAME               ID", "meina:latest       abc"]


class _Completed:
    returncode = 0
    stdout = _Output()
    stderr = ""


def main() -> int:
    source = (ROOT / "meina_health.py").read_text(encoding="utf-8")
    assert "REQUIRED_EXECUTABLES" in source
    assert "OLLAMA_MODEL = \"meina\"" in source
    assert "def _check_ollama_model" in source
    assert "def _check_cuda_dlls" in source
    assert "nvidia-smi" in source
    assert ".venv_new" in source
    assert ".venv" in source
    assert "WHISPER_CACHE_DIR_NAME" in source
    assert "def _check_whisper_cache" in source

    original_which = meina_health.shutil.which
    original_run = meina_health.subprocess.run
    try:
        meina_health.shutil.which = lambda name: "C:\\ollama.exe" if name == "ollama" else None
        meina_health.subprocess.run = lambda *args, **kwargs: _Completed()
        ok, detail = meina_health._check_ollama_model()
        assert ok, detail
        assert "meina" in detail.lower()

        class _Missing:
            returncode = 0
            stdout = "NAME               ID\nother:latest       xyz\n"
            stderr = ""

        meina_health.subprocess.run = lambda *args, **kwargs: _Missing()
        ok, detail = meina_health._check_ollama_model()
        assert not ok
        assert "meina" in detail.lower()

        class _Failed:
            returncode = 1
            stdout = ""
            stderr = "connection refused"

        meina_health.subprocess.run = lambda *args, **kwargs: _Failed()
        ok, detail = meina_health._check_ollama_model()
        assert not ok
        assert "service unavailable" in detail.lower()
    finally:
        meina_health.shutil.which = original_which
        meina_health.subprocess.run = original_run

    original_home = meina_health.Path.home
    original_env = meina_health.os.environ.get("HF_HOME")
    try:
        meina_health.Path.home = classmethod(lambda cls: Path("/nonexistent/meina-test-home"))
        meina_health.os.environ["HF_HOME"] = "/nonexistent/meina-hf"
        status, detail = meina_health._check_whisper_cache()
        assert status == "WARN"
        assert "first startup may download" in detail
    finally:
        meina_health.Path.home = original_home
        if original_env is None:
            meina_health.os.environ.pop("HF_HOME", None)
        else:
            meina_health.os.environ["HF_HOME"] = original_env

    print("Health core self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
