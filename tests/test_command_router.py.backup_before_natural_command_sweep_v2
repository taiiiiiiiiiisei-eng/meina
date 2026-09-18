import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import command_router


def assert_weather(text, expected_mode):
    route = command_router.route_command(text, {"confidence": 1.0})
    assert route is not None, f"route is None: {text}"
    assert route["kind"] == "weather", route
    assert route["query"] == expected_mode, route


def assert_route(text, kind, target=None, query=None, confidence=1.0):
    route = command_router.route_command(text, {"confidence": confidence})
    assert route is not None, f"route is None: {text}"
    assert route["kind"] == kind, route
    if target is not None:
        assert route["target"] == target, route
    if query is not None:
        assert route["query"] == query, route
    return route


def main():
    assert_weather("今日の天気を教えて", "today")
    assert_weather("明日の天気を教えて", "tomorrow")
    assert_weather("今の気温は？", "current_temp")
    assert_weather("今日雨降る？", "rain")
    assert_weather("明日の雨降る？", "rain")

    location_route = command_router.route_command(
        "東京の明日の天気を教えて",
        {"confidence": 1.0},
    )
    assert location_route is not None, location_route
    assert location_route["kind"] == "weather", location_route
    assert location_route["target"] == "東京", location_route
    assert location_route["query"] == "tomorrow", location_route

    assert_route(
        "東京の今の気温は？",
        "weather",
        target="東京",
        query="current_temp",
    )
    assert_route(
        "東京の雨降る？",
        "weather",
        target="東京",
        query="rain",
    )

    assert_route(
        "GoogleでVALORANTを検索して",
        "web_search",
        target="google",
        query="valorant",
    )
    assert_route(
        "YouTubeを開いて",
        "web_open",
        target="youtube",
    )
    assert_route(
        "メモ帳を開いて",
        "app_open",
        target="notepad",
    )
    assert_route(
        "VALOやる",
        "app_open",
        target="VALORANT",
    )

    assert_route("今何時？", "time", target="local")
    assert_route("今日は何日？", "date", target="local")
    assert_route("今日は何曜日？", "weekday", target="local")
    assert_route("PCの状態を教えて", "pc_status", target="pc")
    assert_route("今日の配信の切り抜きを作って", "twitch_clip", target="latest")
    assert_route("明日雨降る？", "weather", target="current", query="rain")

    assert command_router.route_command(
        "こんにちは、元気？",
        {"confidence": 0.10},
    ) is None

    print("ALL ROUTER TESTS PASSED")


if __name__ == "__main__":
    main()
