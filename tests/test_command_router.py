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


def main():
    assert_weather("今日の天気を教えて", "today")
    assert_weather("明日の天気を教えて", "tomorrow")
    assert_weather("今の気温は？", "current_temp")
    assert_weather("今日雨降る？", "rain")

    location_route = command_router.route_command(
        "東京の明日の天気を教えて",
        {"confidence": 1.0},
    )
    assert location_route is not None, location_route
    assert location_route["kind"] == "weather", location_route
    assert location_route["target"] == "東京", location_route
    assert location_route["query"] == "tomorrow", location_route

    print("ALL ROUTER TESTS PASSED")


if __name__ == "__main__":
    main()
