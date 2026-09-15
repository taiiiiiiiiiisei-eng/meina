from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _wmic_value(command: list[str]) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines[-1] if lines else None
    except Exception:
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

    total_kb = _wmic_value(["wmic", "computersystem", "get", "TotalPhysicalMemory"])
    if total_kb and total_kb.isdigit():
        status["ram_total_gb"] = round(int(total_kb) / 1024**3, 1)

    free_kb = _wmic_value(["wmic", "os", "get", "FreePhysicalMemory"])
    if free_kb and free_kb.isdigit():
        status["ram_free_gb"] = round(int(free_kb) / 1024**2, 1)

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        gpu = next((line.strip() for line in result.stdout.splitlines() if line.strip()), None)
        if gpu:
            status["gpu"] = gpu
    except Exception:
        pass

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
