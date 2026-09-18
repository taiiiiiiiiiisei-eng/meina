import subprocess
import webbrowser
import os
import glob
from datetime import datetime
from urllib.parse import quote


# ==========================================
# 日付・時刻
# ==========================================

def get_date():
    now = datetime.now()
    return f"今日は{now.year}年{now.month}月{now.day}日です。"


def get_time():
    now = datetime.now()
    return f"現在は{now.hour}時{now.minute}分です。"


def get_weekday():
    weekdays = [
        "月曜日",
        "火曜日",
        "水曜日",
        "木曜日",
        "金曜日",
        "土曜日",
        "日曜日"
    ]

    return f"今日は{weekdays[datetime.now().weekday()]}です。"


# ==========================================
# Windows標準アプリ
# ==========================================

def open_notepad():
    subprocess.Popen(["notepad.exe"])
    return "メモ帳を開きました。"


def open_calculator():
    subprocess.Popen(["calc.exe"])
    return "電卓を開きました。"


def open_explorer():
    subprocess.Popen(["explorer.exe"])
    return "エクスプローラーを開きました。"


# ==========================================
# Web
# ==========================================

def open_google():
    webbrowser.open("https://www.google.com")
    return "Googleを開きました。"


def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "YouTubeを開きました。"


def open_browser():
    webbrowser.open("https://www.google.com")
    return "ブラウザを開きました。"


def google_search(query):
    url = "https://www.google.com/search?q=" + quote(query)
    webbrowser.open(url)
    return f"Googleで「{query}」を検索しました。"


def youtube_search(query):
    url = "https://www.youtube.com/results?search_query=" + quote(query)
    webbrowser.open(url)
    return f"YouTubeで「{query}」を検索しました。"


# ==========================================
# 天気
# ==========================================

def get_weather(location=None, mode="today"):
    """wttr.inから今日/明日/現在気温の天気情報を取得する。APIキー不要。"""
    import requests

    target = str(location or "").strip()
    url = "https://wttr.in/" + (quote(target) if target else "") + "?format=j1&lang=ja"

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Meina/1.0"},
        )
        response.raise_for_status()
        data = response.json()

        current = data["current_condition"][0]
        forecast = data.get("weather", [])
        today = forecast[0]
        tomorrow = forecast[1] if len(forecast) > 1 else None
        area = data.get("nearest_area", [{}])[0]
        area_name = area.get("areaName", [{}])[0].get("value", "現在地")
        condition = current.get("lang_ja", [{}])[0].get("value") or current.get("weatherDesc", [{}])[0].get("value", "")
        temp = current.get("temp_C", "-")
        feels = current.get("FeelsLikeC", "-")

        if mode == "current_temp":
            return f"現在の気温は{temp}℃です。体感温度は{feels}℃です。"

        if mode == "rain":
            rain_target = tomorrow if ("明日" in target or "あす" in target) and tomorrow else today
            hours = rain_target.get("hourly", [])
            probabilities = []
            for hour in hours:
                value = hour.get("chanceofrain")
                try:
                    probabilities.append(int(value))
                except (TypeError, ValueError):
                    pass
            max_rain = max(probabilities) if probabilities else 0
            if target:
                headline = f"{area_name}の"
            else:
                headline = ""
            if max_rain >= 70:
                advice = "傘を持っていくのがおすすめです。"
            elif max_rain >= 40:
                advice = "雨に備えて、傘があると安心です。"
            else:
                advice = "雨の可能性は低めです。"
            return headline + f"降水確率は最大{max_rain}%です。" + advice

        if mode == "tomorrow" and tomorrow:
            condition = (
                tomorrow.get("hourly", [{}])[0].get("lang_ja", [{}])[0].get("value")
                or tomorrow.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", "")
            )
            max_temp = tomorrow.get("maxtempC", "-")
            min_temp = tomorrow.get("mintempC", "-")
            if target:
                headline = f"{area_name}の明日の天気は{condition}です。"
            else:
                headline = f"明日の天気は{condition}です。"
            return headline + f"最高{max_temp}℃、最低{min_temp}℃です。"

        max_temp = today.get("maxtempC", "-")
        min_temp = today.get("mintempC", "-")
        if target:
            headline = f"{area_name}の今日の天気は{condition}です。"
        else:
            headline = f"今日の天気は{condition}です。"

        return headline + f"現在{temp}℃、体感{feels}℃、最高{max_temp}℃、最低{min_temp}℃です。"
    except Exception as e:
        print("天気取得エラー:", e)
        return "天気情報を取得できませんでした。インターネット接続を確認してください。"


# ==========================================
# アプリ検索
# ==========================================

APP_ALIASES = {
    "discord": [
        "Discord.exe"
    ],

    "ディスコード": [
        "Discord.exe"
    ],

    "steam": [
        "Steam.exe"
    ],

    "スチーム": [
        "Steam.exe"
    ],

    "chrome": [
        "chrome.exe"
    ],

    "クローム": [
        "chrome.exe"
    ],

    "edge": [
        "msedge.exe"
    ],

    "エッジ": [
        "msedge.exe"
    ],

    "obs": [
        "obs64.exe",
        "obs32.exe"
    ],

    "オービーエス": [
        "obs64.exe",
        "obs32.exe"
    ],

    "valorant": [
        "VALORANT-Win64-Shipping.exe"
    ],

    "バロラント": [
        "VALORANT-Win64-Shipping.exe"
    ],

    "apex": [
        "r5apex.exe"
    ],

    "エーペックス": [
        "r5apex.exe"
    ],

    "エペ": [
        "r5apex.exe"
    ]
}


def find_exe(exe_names):

    search_dirs = [
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("PROGRAMFILES", ""),
        os.environ.get("PROGRAMFILES(X86)", "")
    ]

    for base_dir in search_dirs:

        if not base_dir:
            continue

        for exe_name in exe_names:

            pattern = os.path.join(
                base_dir,
                "**",
                exe_name
            )

            try:

                matches = glob.glob(
                    pattern,
                    recursive=True
                )

                if matches:
                    return matches[0]

            except Exception:
                pass

    return None


def launch_app(app_name):

    normalized = (
        app_name
        .lower()
        .replace(" ", "")
        .replace("　", "")
    )

    # --------------------------------------
    # アプリを検索
    # --------------------------------------

    exe_names = None

    for alias, names in APP_ALIASES.items():

        if alias in normalized:
            exe_names = names
            break

    if exe_names is None:
        return f"{app_name}は対応していないアプリです。"


    print(f"🔎 {app_name}を探しています...")


    path = find_exe(exe_names)


    if not path:
        return f"{app_name}が見つかりませんでした。"


    print(f"📍 発見: {path}")


    try:

        if (
            normalized == "obs"
            and os.path.normcase(path) == os.path.normcase(
                r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
            )
        ):
            subprocess.Popen(
                [path],
                cwd=r"C:\Program Files\obs-studio\bin\64bit"
            )
        else:
            subprocess.Popen([path])

        return f"{app_name}を起動しました。"

    except Exception as e:

        print("アプリ起動エラー:", e)

        return f"{app_name}を起動できませんでした。"
