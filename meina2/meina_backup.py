import os
import json
import subprocess
import webbrowser
from datetime import datetime

# ==========================================
# 基本設定
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)


# ==========================================
# CUDA DLL
# ==========================================

SITE_PACKAGES = os.path.join(
    PARENT_DIR,
    ".venv",
    "Lib",
    "site-packages"
)

CUBLAS_BIN = os.path.join(
    SITE_PACKAGES,
    "nvidia",
    "cublas",
    "bin"
)

CUDNN_BIN = os.path.join(
    SITE_PACKAGES,
    "nvidia",
    "cudnn",
    "bin"
)

if os.path.exists(CUBLAS_BIN):
    os.add_dll_directory(CUBLAS_BIN)

if os.path.exists(CUDNN_BIN):
    os.add_dll_directory(CUDNN_BIN)

os.environ["PATH"] = (
    CUBLAS_BIN
    + os.pathsep
    + CUDNN_BIN
    + os.pathsep
    + os.environ["PATH"]
)


# ==========================================
# ライブラリ
# ==========================================

import sounddevice as sd
import pyttsx3
import ollama

from faster_whisper import WhisperModel


# ==========================================
# Whisper
# ==========================================

print("🧠 Whisperを起動しています...")

whisper = WhisperModel(
    config["whisper_model"],
    device="cuda",
    compute_type="float16"
)

print("✅ Whisper起動成功！")


# ==========================================
# 音声入力
# ==========================================

SAMPLE_RATE = 16000


def listen(seconds=7):

    print("🎙️ 聞いています...")

    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    audio = audio.flatten()

    print("🧠 音声を解析中...")

    segments, info = whisper.transcribe(
        audio,
        language="ja",
        beam_size=5
    )

    text = ""

    for segment in segments:
        text += segment.text

    text = text.strip()

    print("👂 認識：" + text)

    return text


# ==========================================
# 音声出力
# ==========================================

def speak(text):

    print("🔊 めいな：" + text)

    engine = pyttsx3.init()

    engine.setProperty(
        "rate",
        config["voice_rate"]
    )

    engine.say(text)
    engine.runAndWait()

    engine.stop()


# ==========================================
# ウェイクワード
# ==========================================

wake_words = [
    "めいな",
    "メイナ",
    "メインな",
    "女 いい なぁ",
    "名 なぁ",
    "メイン な"
]


def find_wake_word(text):

    for word in wake_words:

        if word in text:
            return word

    return None


def get_command(text):

    for word in wake_words:

        if word in text:

            command = text.split(
                word,
                1
            )[1]

            return (
                command
                .replace(" ", "")
                .replace("　", "")
                .strip()
            )

    return ""


# ==========================================
# PCツール
# ==========================================

def open_notepad():

    subprocess.Popen(
        "notepad.exe"
    )


def open_calculator():

    subprocess.Popen(
        "calc.exe"
    )


def open_explorer():

    subprocess.Popen(
        "explorer.exe"
    )


def open_google():

    webbrowser.open(
        "https://www.google.com"
    )


def open_youtube():

    webbrowser.open(
        "https://www.youtube.com"
    )


# ==========================================
# AIに質問
# ==========================================

def ask_ai(command):

    print("🧠 めいなが考えています...")

    response = ollama.chat(
        model=config["ollama_model"],
        messages=[
            {
                "role": "user",
                "content": command
            }
        ]
    )

    return response["message"]["content"].strip()


# ==========================================
# コマンド処理
# ==========================================

def execute(command):

    command = (
        command
        .replace(" ", "")
        .replace("　", "")
        .strip()
    )

    if not command:
        return True


    # ------------------------------
    # 終了
    # ------------------------------

    if command in [
        "終了",
        "終わって",
        "おわり",
        "バイバイ"
    ]:

        speak("終了します。")

        return "EXIT"


    # ------------------------------
    # 日付
    # ------------------------------

    if (
        "今日" in command
        and (
            "何日" in command
            or "日付" in command
        )
    ):

        now = datetime.now()

        speak(
            f"今日は{now.year}年"
            f"{now.month}月"
            f"{now.day}日です。"
        )

        return True


    # ------------------------------
    # 曜日
    # ------------------------------

    if (
        "今日" in command
        and "何曜日" in command
    ):

        now = datetime.now()

        weekdays = [
            "月曜日",
            "火曜日",
            "水曜日",
            "木曜日",
            "金曜日",
            "土曜日",
            "日曜日"
        ]

        speak(
            f"今日は"
            f"{weekdays[now.weekday()]}"
            f"です。"
        )

        return True


    # ------------------------------
    # 時刻
    # ------------------------------

    if (
        "今何時" in command
        or "現在時刻" in command
        or "今の時間" in command
    ):

        now = datetime.now()

        speak(
            f"現在は{now.hour}時"
            f"{now.minute}分です。"
        )

        return True


    # ------------------------------
    # メモ帳
    # ------------------------------

    if "メモ帳" in command:

        speak("メモ帳を開きます。")

        open_notepad()

        return True


    # ------------------------------
    # 電卓
    # ------------------------------

    if "電卓" in command:

        speak("電卓を開きます。")

        open_calculator()

        return True


    # ------------------------------
    # エクスプローラー
    # ------------------------------

    if "エクスプローラー" in command:

        speak(
            "エクスプローラーを開きます。"
        )

        open_explorer()

        return True


    # ------------------------------
    # Google
    # ------------------------------

    if (
        "Google" in command
        or "グーグル" in command
    ):

        speak("Googleを開きます。")

        open_google()

        return True


    # ------------------------------
    # YouTube
    # ------------------------------

    if (
        "YouTube" in command
        or "ユーチューブ" in command
    ):

        speak("YouTubeを開きます。")

        open_youtube()

        return True


    # ------------------------------
    # 分からない命令
    # → AIへ
    # ------------------------------

    answer = ask_ai(command)

    speak(answer)

    return True


# ==========================================
# 起動
# ==========================================

print()
print("================================")
print("🤖 めいな2.0")
print("================================")

speak("起動しました。")


# ==========================================
# メインループ
# ==========================================

while True:

    print()
    print("💤 待機中……")

    # ------------------------------
    # ウェイクワード待機
    # ------------------------------

    while True:

        text = listen(7)

        wake = find_wake_word(text)

        if wake:

            command = get_command(text)

            # --------------------------
            # 「めいな」だけ
            # --------------------------

            if not command:

                speak(
                    "はい、どうしました？"
                )

                command = listen(7)

                command = (
                    command
                    .replace(" ", "")
                    .replace("　", "")
                    .strip()
                )

            break


    # ------------------------------
    # 実行
    # ------------------------------

    result = execute(command)

    if result == "EXIT":
        break