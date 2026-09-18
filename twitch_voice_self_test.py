from __future__ import annotations

from meina_twitch_intent import is_twitch_clip_request


CASES = {
    "昨日の配信切り抜いて": True,
    "今日の配信をハイライトにして": True,
    "Twitchの最近の配信切り抜いて": True,
    "メモ帳を開いて": False,
}


def main() -> int:
    failed = False
    for text, expected in CASES.items():
        actual = is_twitch_clip_request(text)
        status = "OK" if actual == expected else "FAIL"
        print(f"{status}: {text!r} -> {actual}")
        if actual != expected:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
