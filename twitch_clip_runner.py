from __future__ import annotations

import sys
from pathlib import Path

from meina_twitch import run_twitch_clip_command


def main() -> int:
    text = " ".join(sys.argv[1:]).strip() or "昨日の配信切り抜いて"
    result = run_twitch_clip_command(text)
    if not result.get("ok"):
        print(result.get("message", "切り抜き命令ではありません"))
        return 1
    print(result["message"])
    for clip in result.get("clips", []):
        print(Path(clip))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
