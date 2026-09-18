from __future__ import annotations

from meina_twitch import _requested_day, is_twitch_clip_request


def main() -> int:
    cases = {
        "昨日の配信切り抜いて": "yesterday",
        "今日の配信をハイライトにして": "today",
        "最近の配信を切り抜いて": None,
    }
    failed = False
    for text, expected in cases.items():
        actual = _requested_day(text)
        print(("OK" if actual == expected else "FAIL"), "day:", text, "->", actual)
        failed |= actual != expected

    routing_cases = {
        "昨日の配信切り抜いて": True,
        "Twitchの配信をハイライトにして": True,
        "メモ帳を開いて": False,
        "VALORANTを検索して": False,
    }
    for text, expected in routing_cases.items():
        actual = is_twitch_clip_request(text)
        print(("OK" if actual == expected else "FAIL"), "route:", text, "->", actual)
        failed |= actual != expected

    print("Twitch command test: FAIL" if failed else "Twitch command test: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
