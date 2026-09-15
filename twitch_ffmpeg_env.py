from __future__ import annotations

import os
from pathlib import Path


def find_executable(name: str) -> str:
    """Find an executable from PATH or common Windows WinGet locations."""
    path_value = os.environ.get("PATH", "")
    for directory in path_value.split(os.pathsep):
        if not directory:
            continue
        candidate = Path(directory) / name
        if candidate.exists():
            return str(candidate)
        if not name.lower().endswith(".exe"):
            candidate = Path(directory) / f"{name}.exe"
            if candidate.exists():
                return str(candidate)

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        packages = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if packages.exists():
            for candidate in packages.rglob(f"{name}.exe"):
                return str(candidate)

    raise FileNotFoundError(f"{name} が見つかりません。FFmpegをインストールしてPATHを確認してください。")


if __name__ == "__main__":
    print("ffmpeg:", find_executable("ffmpeg"))
    print("ffprobe:", find_executable("ffprobe"))
