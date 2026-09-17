from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _run_text(command: list[str], timeout: int = 3) -> str | None:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _number_from_output(text: str | None) -> float | None:
    if not text:
        return None
    for line in reversed(text.splitlines()):
        value = line.strip()
        if value.isdigit():
            return float(value)
    return None


def get_pc_status() -> dict[str, str | int | float | None]:
    """Return read-only, low-risk PC status information."""
    status: dict[str, str | int | float | None] = {
        "disk_free_gb": None,
        "disk_total_gb": None,
        "ram_total_gb": None,
        "ram_free_gb": None,
        "gpu": None,
    }

    try:
        usage = shutil.disk_usage(Path.home().anchor or "C:\\")
        status["disk_free_gb"] = round(usage.free / 1024**3, 1)
        status["disk_total_gb"] = round(usage.total / 1024**3, 1)
    except Exception:
        pass

    # WMIC is deprecated/absent on some Windows versions, so prefer CIM and fall back to WMIC.
    total_text = _run_text([
        "powershell", "-NoProfile", "-Command",
        "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory",
    ])
    total_bytes = _number_from_output(total_text)
    if total_bytes is None:
        total_bytes = _number_from_output(
            _run_text(["wmic", "computersystem", "get", "TotalPhysicalMemory"])
        )
    if total_bytes is not None:
        status["ram_total_gb"] = round(total_bytes / 1024**3, 1)

    free_text = _run_text([
        "powershell", "-NoProfile", "-Command",
        "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory",
    ])
    free_kb = _number_from_output(free_text)
    if free_kb is None:
        free_kb = _number_from_output(
            _run_text(["wmic", "os", "get", "FreePhysicalMemory"])
        )
    if free_kb is not None:
        status["ram_free_gb"] = round(free_kb / 1024**2, 1)

    gpu_output = _run_text([
        "nvidia-smi", "--query-gpu=name", "--format=csv,noheader"
    ])
    if gpu_output:
        gpu = next((line.strip() for line in gpu_output.splitlines() if line.strip()), None)
        if gpu:
            status["gpu"] = gpu

    return status


def format_pc_status(status: dict[str, str | int | float | None]) -> str:
    parts = []
    if status.get("gpu"):
        parts.append(f"GPUは{status['gpu']}です")
    if status.get("ram_free_gb") is not None and status.get("ram_total_gb") is not None:
        parts.append(f"メモリ空きは{status['ram_free_gb']}GB、合計{status['ram_total_gb']}GBです")
    if status.get("disk_free_gb") is not None and status.get("disk_total_gb") is not None:
        parts.append(f"ディスク空きは{status['disk_free_gb']}GB、合計{status['disk_total_gb']}GBです")
    return "。".join(parts) + ("。" if parts else "PC状態を取得できませんでした。")


if __name__ == "__main__":
    print(format_pc_status(get_pc_status()))
