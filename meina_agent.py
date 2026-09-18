import os
import time

import sounddevice as sd
import pyttsx3
import ollama

import command_router
from meina_task_plans import get_task_plan, validate_task_plan

# MEINA_UPGRADE_TASK_PLAN_LOCAL_V1


# =========================================================
# 基本設定
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("============================================================")
print("🤖 めいな Voice Agent")
print("============================================================")


# =========================================================
# CUDA DLL設定
# =========================================================

possible_site_packages = [
    os.path.join(
        BASE_DIR,
        ".venv",
        "Lib",
        "site-packages"
    ),

    os.path.join(
        os.path.dirname(BASE_DIR),
        ".venv",
        "Lib",
        "site-packages"
    )
]

SITE_PACKAGES = None

for path in possible_site_packages:
    if os.path.exists(path):
        SITE_PACKAGES = path
        break

if SITE_PACKAGES is None:
    SITE_PACKAGES = possible_site_packages[-1]


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


print("CUDA設定")

print("CUBLAS:", CUBLAS_BIN)
print("CUDNN :", CUDNN_BIN)


if os.path.exists(CUBLAS_BIN):

    try:
        os.add_dll_directory(
            CUBLAS_BIN
        )
    except Exception:
        pass


if os.path.exists(CUDNN_BIN):

    try:
        os.add_dll_directory(
            CUDNN_BIN
        )
    except Exception:
        pass


os.environ["PATH"] = (
    CUBLAS_BIN
    + os.pathsep
    + CUDNN_BIN
    + os.pathsep
    + os.environ.get("PATH", "")
)


# =========================================================
# Whisper
# =========================================================

print("")
print("🧠 faster-whisper large-v3 を起動しています...")
print("GPU: CUDA")
print("計算方式: float16")


from faster_whisper import WhisperModel


try:

    whisper_model = WhisperModel(
        "large-v3",
        device="cuda",
        compute_type="float16"
    )

    print("✅ Whisper 起動完了")

except Exception as e:

    print("❌ Whisper起動エラー:")
    print(e)

    raise


# =========================================================
# brain_core
# =========================================================

print("")
print("🧠 自作AI brain_core v3.6 を読み込んでいます...")


try:

    from meina_brain import brain_core

    print("✅ brain_core v3.6 接続完了")

except Exception as e:

    print("❌ brain_core読み込みエラー:")
    print(e)

    raise


# =========================================================
# PC操作 tools
# =========================================================

print("")
print("🖥️ PC操作ツールを読み込んでいます...")


try:

    from meina2 import tools

    print("✅ tools 接続完了")

except Exception as e:

    print("❌ tools読み込みエラー:")
    print(e)

    raise


# =========================================================
# TTS
# =========================================================

engine = pyttsx3.init()

engine.setProperty(
    "rate",
    170
)


try:

    voices = engine.getProperty(
        "voices"
    )

    japanese_voice_found = False

    for voice in voices:

        voice_name = voice.name.lower()

        if (
            "haruka" in voice_name
            or "japanese" in voice_name
            or "日本語" in voice.name
        ):

            engine.setProperty(
                "voice",
                voice.id
            )

            print(
                "🔊 音声:",
                voice.name
            )

            japanese_voice_found = True

            break

    if not japanese_voice_found:

        print(
            "⚠️ 日本語音声が見つかりませんでした"
        )

except Exception as e:

    print(
        "⚠️ 音声設定エラー:",
        e
    )


def speak(text):
    """
    めいなの音声出力
    """

    if not text:
        return

    print(
        "🔊 めいな:",
        text
    )

    try:

        engine.say(
            text
        )

        engine.runAndWait()

    except Exception as e:

        print(
            "❌ TTS ERROR:",
            e
        )


# =========================================================
# 音声録音
# =========================================================

SAMPLE_RATE = 16000
AUDIO_DTYPE = "float32"
AUDIO_MIN_RMS = 0.008
AUDIO_SILENCE_PAD = 0.18


def record_audio(duration):
    """
    指定秒数録音
    """

    print(
        f"🎤 録音中... ({duration:.1f}秒)"
    )

    try:

        audio = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=AUDIO_DTYPE,
        )

        sd.wait()

        return preprocess_audio(audio.flatten())

    except Exception as e:

        print(
            "❌ マイクエラー:",
            e
        )

        return None


def preprocess_audio(audio):
    """Whisperへ渡す前に音量差と前後の無音を軽く整える。"""
    if audio is None or len(audio) == 0:
        return audio
    audio = audio.astype("float32", copy=False)
    audio = audio - float(audio.mean())
    peak = float(abs(audio).max())
    rms = float((audio * audio).mean() ** 0.5)
    if peak > 0 and rms >= AUDIO_MIN_RMS:
        audio = audio * min(0.95 / peak, 3.0)
    threshold = max(AUDIO_MIN_RMS, float(abs(audio).max()) * 0.035)
    active = abs(audio) >= threshold
    if active.any():
        indices = active.nonzero()[0]
        pad = int(AUDIO_SILENCE_PAD * SAMPLE_RATE)
        audio = audio[max(0, int(indices[0]) - pad):min(len(audio), int(indices[-1]) + pad + 1)]
    return audio


# =========================================================
# Whisper音声認識
# =========================================================

def transcribe_audio(audio):
    """
    録音音声をWhisperで日本語認識
    """

    if audio is None:
        return ""

    try:

        segments, info = whisper_model.transcribe(
            audio,
            language="ja",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 350,
                "speech_pad_ms": 250,
            },
            condition_on_previous_text=False,
            initial_prompt=(
                "日本語の音声アシスタント。めいな、VALORANT、バロラント、バロ、VALO、"
                "Apex、エーペックス、エペ、Discord、OBS、Google、YouTube、Twitch、"
                "UVERworldなどの固有名詞を正確に認識する。"
            ),
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )

        text = ""

        for segment in segments:

            text += segment.text

        text = text.strip()

        # Whisperの聞き間違いを補正
        text = correct_recognition(text)

        return text

    except Exception as e:

        print(
            "❌ Whisperエラー:",
            e
        )

        return ""


def listen(duration=4.0):
    """
    録音 → Whisper認識
    """

    audio = record_audio(
        duration
    )

    if audio is None:
        return ""

    text = transcribe_audio(
        audio
    )

    if text:

        print(
            "🎤 認識:",
            text
        )

    return text


# =========================================================
# ウェイクワード
# =========================================================

WAKE_WORDS = [
    "めいな",
    "メイナ",
    "メイナー"
]


def correct_recognition(text):
    """
    Whisperで起きやすい日本語・固有名詞の聞き間違いを補正
    """

    if not text:
        return ""

    corrections = [
        ("メイナー", "メイナ"),
        ("めいナー", "めいな"),
        ("メイナァ", "メイナ"),
        ("バロラン", "バロラント"),
        ("ばろらん", "バロラント"),
        ("Uberworld", "UVERworld"),
        ("Uber World", "UVERworld"),
        ("ユーバーワールド", "UVERworld"),
        ("ウーバーワールド", "UVERworld"),
        ("ディスコート", "Discord"),
        ("ディスコード", "Discord"),
        ("ユーチューブ", "YouTube"),
        ("ゆーちゅーぶ", "YouTube"),
        ("グーグル", "Google"),
        ("ぐーぐる", "Google"),
        ("エモ帳", "メモ帳"),
        ("えも帳", "メモ帳"),
    ]

    result = text

    for before, after in corrections:
        result = result.replace(before, after)

    return result


def normalize_text(text):
    """
    Whisper結果を簡単に正規化
    """

    if not text:
        return ""

    result = text

    result = result.replace(
        " ",
        ""
    )

    result = result.replace(
        "　",
        ""
    )

    return result


def contains_wake_word(text):
    """
    めいなが呼ばれたか判定
    """

    if not text:
        return False

    normalized = normalize_text(
        text
    )

    for word in WAKE_WORDS:

        if word in normalized:

            return True

    return False


def remove_wake_word(text):
    """
    ウェイクワードを命令から削除
    """

    if not text:
        return ""

    result = text

    # 長いものから先に削除
    words = sorted(
        WAKE_WORDS,
        key=len,
        reverse=True
    )

    for word in words:

        result = result.replace(
            word,
            ""
        )

    # Whisperが付ける可能性のある記号などを削除
    result = result.strip(
        " 、,。.!！?？"
    )

    # -----------------------------------------------------
    # 重要
    #
    # 「メイナー」
    # ↓
    # 「ー」
    #
    # のような誤認識を除外する
    # -----------------------------------------------------

    result = result.strip(
        "ー―—-"
    )

    result = result.strip(
        " 、,。.!！?？"
    )

    return result


def is_invalid_command(text):
    """
    命令として扱うには短すぎる
    誤認識を判定
    """

    if not text:
        return True

    value = text.strip()

    if not value:
        return True

    invalid_values = [
        "ー",
        "――",
        "―",
        "—",
        "-",
        "--",
        "?",
        "？",
        ".",
        "。",
        ",",
        "、",
        "!",
        "！",
        "あ",
        "え",
        "ん"
    ]

    if value in invalid_values:
        return True

    # 記号だけの場合
    symbol_only = True

    for char in value:

        if char.isalnum():
            symbol_only = False
            break

        if (
            "\u3040"
            <= char
            <= "\u30ff"
        ):
            symbol_only = False
            break

        if (
            "\u4e00"
            <= char
            <= "\u9fff"
        ):
            symbol_only = False
            break

    if symbol_only:
        return True

    return False


# =========================================================
# PC操作
# =========================================================

def _execute_routed_command_base(route):
    """command_router が許可した固定コマンドだけを実行する。"""
    kind = route["kind"]
    target = route["target"]
    query = route["query"]

    try:
        if kind == "app_open":
            app_functions = {
                "notepad": tools.open_notepad,
                "calculator": tools.open_calculator,
                "explorer": tools.open_explorer,
            }
            result = app_functions.get(target, lambda: tools.launch_app(target))()
        elif kind == "web_open":
            web_functions = {
                "google": tools.open_google,
                "youtube": tools.open_youtube,
            }
            result = web_functions[target]()
        elif kind == "web_search":
            search_functions = {
                "google": tools.google_search,
                "youtube": tools.youtube_search,
            }
            result = search_functions[target](query)
        else:
            return False

        print("🛡️ 許可済みPC操作:", route)
        speak(result)
        return True

    except Exception as e:
        print("❌ PC操作エラー:", e)
        speak("PC操作を実行できませんでした")
        return True


# MEINA_UPGRADE_TASK_PLAN_LOCAL_V1_EXEC

def execute_task_plan(route):
    """安全な固定タスクだけを順番に実行する。"""
    plan_name = route.get("target")
    if not plan_name or not validate_task_plan(plan_name):
        print("⚠️ 不正なタスク計画のため実行しません")
        return False

    plan = get_task_plan(plan_name)
    print("")
    print("🧩 固定タスク計画:", plan_name)

    for index, step in enumerate(plan, 1):
        print(f"  [{index}/{len(plan)}] {step['label']}")
        step_route = {
            "kind": step["kind"],
            "target": step["target"],
            "query": step.get("query"),
            "confidence": 1.0,
        }
        if not _execute_routed_command_base(step_route):
            print("❌ タスク計画を中断:", step["label"])
            speak("配信準備を中断しました")
            return True

    print("✅ 配信準備完了")
    completion_messages = {
        "stream_prepare_valorant": "VALORANTの配信準備が完了しました",
        "stream_prepare_apex": "Apex Legendsの配信準備が完了しました",
    }
    speak(completion_messages.get(plan_name, "配信準備が完了しました"))
    return True


def execute_routed_command(route):
    if route.get("kind") == "task_plan":
        return execute_task_plan(route)
    return _execute_routed_command_base(route)


def execute_action(frame):
    """
    brain_core v3.6の解析結果を
    PC操作へ変換
    """

    if not frame:
        return False

    target = frame.get(
        "target"
    )

    action = frame.get(
        "action"
    )

    confidence = frame.get(
        "confidence",
        0
    )

    print("")
    print("🎯 AI行動判断")

    print(
        "target     :",
        target
    )

    print(
        "action     :",
        action
    )

    print(
        "confidence :",
        confidence
    )

    print(
        "words      :",
        frame.get("words")
    )

    print("")

    # -----------------------------------------------------
    # 対象や動作が取れていない
    # -----------------------------------------------------

    if not target or not action:

        return False

    # -----------------------------------------------------
    # 信頼度チェック
    # -----------------------------------------------------

    if confidence < 0.70:

        print(
            "⚠️ 信頼度が低いためPC操作を実行しません"
        )

        return False

    # =====================================================
    # メモ帳
    # =====================================================

    if (
        target == "メモ帳"
        and action == "開く"
    ):

        try:

            tools.open_notepad()

            speak(
                "メモ帳を開きました"
            )

            return True

        except Exception as e:

            print(
                "❌ メモ帳エラー:",
                e
            )

            speak(
                "メモ帳を開けませんでした"
            )

            return True

    # =====================================================
    # 電卓
    # =====================================================

    if (
        target in [
            "電卓",
            "計算機"
        ]
        and action == "開く"
    ):

        try:

            tools.open_calculator()

            speak(
                "電卓を開きました"
            )

            return True

        except Exception as e:

            print(
                "❌ 電卓エラー:",
                e
            )

            speak(
                "電卓を開けませんでした"
            )

            return True

    # =====================================================
    # エクスプローラー
    # =====================================================

    if (
        target in [
            "エクスプローラー",
            "Explorer",
            "ファイル"
        ]
        and action == "開く"
    ):

        try:

            tools.open_explorer()

            speak(
                "エクスプローラーを開きました"
            )

            return True

        except Exception as e:

            print(
                "❌ エクスプローラーエラー:",
                e
            )

            speak(
                "エクスプローラーを開けませんでした"
            )

            return True

    # =====================================================
    # Google
    # =====================================================

    if target in [
        "Google",
        "グーグル"
    ]:

        try:

            if action == "検索":

                tools.google_search(
                    target
                )

                speak(
                    "Googleで検索しました"
                )

            else:

                tools.open_google()

                speak(
                    "Googleを開きました"
                )

            return True

        except Exception as e:

            print(
                "❌ Googleエラー:",
                e
            )

            speak(
                "Googleを開けませんでした"
            )

            return True

    # =====================================================
    # YouTube
    # =====================================================

    if target in [
        "YouTube",
        "ユーチューブ"
    ]:

        try:

            if action == "検索":

                tools.youtube_search(
                    target
                )

                speak(
                    "YouTubeで検索しました"
                )

            else:

                tools.open_youtube()

                speak(
                    "YouTubeを開きました"
                )

            return True

        except Exception as e:

            print(
                "❌ YouTubeエラー:",
                e
            )

            speak(
                "YouTubeを開けませんでした"
            )

            return True

    # =====================================================
    # ブラウザ
    # =====================================================

    if target in [
        "ブラウザ",
        "Chrome",
        "クローム"
    ]:

        try:

            if action == "検索":

                tools.google_search(
                    target
                )

                speak(
                    "ブラウザで検索しました"
                )

            else:

                tools.open_browser()

                speak(
                    "ブラウザを開きました"
                )

            return True

        except Exception as e:

            print(
                "❌ ブラウザエラー:",
                e
            )

            speak(
                "ブラウザを開けませんでした"
            )

            return True

    # =====================================================
    # Discord
    # =====================================================

    if target in [
        "Discord",
        "ディスコード"
    ]:

        try:

            tools.launch_app(
                "Discord"
            )

            speak(
                "Discordを開きました"
            )

            return True

        except Exception as e:

            print(
                "❌ Discordエラー:",
                e
            )

            speak(
                "Discordを開けませんでした"
            )

            return True

    # =====================================================
    # Steam
    # =====================================================

    if target in [
        "Steam",
        "スチーム"
    ]:

        try:

            tools.launch_app(
                "Steam"
            )

            speak(
                "Steamを開きました"
            )

            return True

        except Exception as e:

            print(
                "❌ Steamエラー:",
                e
            )

            speak(
                "Steamを開けませんでした"
            )

            return True

    # =====================================================
    # VALORANT
    # =====================================================

    if target in [
        "VALORANT",
        "バロラント"
    ]:

        try:

            tools.launch_app(
                "VALORANT"
            )

            speak(
                "VALORANTを起動しました"
            )

            return True

        except Exception as e:

            print(
                "❌ VALORANTエラー:",
                e
            )

            speak(
                "VALORANTを起動できませんでした"
            )

            return True

    # =====================================================
    # 汎用アプリ起動
    # =====================================================

    if action == "開く":

        try:

            tools.launch_app(
                target
            )

            speak(
                str(target)
                + "を開きました"
            )

            return True

        except Exception as e:

            print(
                "❌ アプリ起動エラー:",
                e
            )

            print(
                "対象:",
                target
            )

            return False

    return False


# =========================================================
# Ollama会話
# =========================================================

def chat_with_meina(text):
    """
    普通の質問をOllamaのめいなへ送る
    """

    if not text:
        return ""

    try:

        response = ollama.chat(
            model="meina",
            messages=[
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        answer = response[
            "message"
        ][
            "content"
        ].strip()

        if not answer:

            answer = "すみません、うまく答えられませんでした。"

        print(
            "🧠 めいな:",
            answer
        )

        speak(
            answer
        )

        return answer

    except Exception as e:

        print(
            "❌ Ollamaエラー:",
            e
        )

        speak(
            "すみません、うまく答えられませんでした"
        )

        return ""


# =========================================================
# 命令処理
# =========================================================

def process_command(text):
    """
    音声で認識した命令を処理
    """

    if not text:
        return

    if is_invalid_command(text):

        print(
            "⚠️ 無効な音声認識を無視:",
            repr(text)
        )

        return

    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(
        "📝 命令:",
        text
    )
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # =====================================================
    # brain_core
    # =====================================================

    try:

        frame = brain_core.extract_action_frame(
            text
        )

        print(
            "🧠 brain_core:",
            frame
        )

    except Exception as e:

        print(
            "❌ brain_core解析エラー:",
            e
        )

        frame = None

    # =====================================================
    # 安全なPC操作
    # =====================================================

    route = command_router.route_command(
        text,
        frame
    )

    if route:

        if execute_routed_command(route):

            return

    # =====================================================
    # 普通の会話
    # =====================================================

    chat_with_meina(
        text
    )


# =========================================================
# ウェイクワード＋命令処理
# =========================================================

def handle_voice_input(text):
    """
    認識した音声から
    ウェイクワードと命令を分離
    """

    if not text:
        return

    print(
        "👂 聞き取り:",
        text
    )

    # =====================================================
    # ウェイクワードがない
    # =====================================================

    if not contains_wake_word(
        text
    ):

        return

    print("")
    print(
        "🎯 ウェイクワード検出！"
    )

    # =====================================================
    # ウェイクワード削除
    # =====================================================

    command = remove_wake_word(
        text
    )

    # =====================================================
    # 無効な命令なら
    # 「メイナだけ」とみなす
    # =====================================================

    if is_invalid_command(
        command
    ):

        command = ""

    # =====================================================
    # メイナだけ
    # =====================================================

    if not command:

        print(
            "🎯 ウェイクワードのみ検出"
        )

        speak(
            "はい、どうしました？"
        )

        print("")
        print(
            "🎤 命令を待っています..."
        )

        command = listen(
            duration=5.0
        )

        if not command:

            print(
                "⚠️ 命令を認識できませんでした"
            )

            return

        print(
            "👂 命令:",
            command
        )

        # =================================================
        # 終了
        # =================================================

        if command.strip() in [
            "終了",
            "終わり",
            "バイバイ",
            "おやすみ"
        ]:

            speak(
                "またね！"
            )

            raise SystemExit

        # =================================================
        # 二重ウェイクワード対策
        # =================================================

        if contains_wake_word(
            command
        ):

            command = remove_wake_word(
                command
            )

        if is_invalid_command(
            command
        ):

            print(
                "⚠️ 無効な命令でした"
            )

            return

    else:

        print(
            "🎯 ウェイクワードと命令を同時認識:",
            command
        )

    # =====================================================
    # Google / YouTube 単体コマンド
    # =====================================================

    normalized_command = normalize_text(command)

    if normalized_command in ["Google", "グーグル"]:

        print("🎯 Google単体コマンド")

        try:
            tools.open_google()
            speak("Googleを開きました")
        except Exception as e:
            print("❌ Googleエラー:", e)
            speak("Googleを開けませんでした")

        return

    if normalized_command in ["YouTube", "ユーチューブ"]:

        print("🎯 YouTube単体コマンド")

        try:
            tools.open_youtube()
            speak("YouTubeを開きました")
        except Exception as e:
            print("❌ YouTubeエラー:", e)
            speak("YouTubeを開けませんでした")

        return

    # =====================================================
    # 命令処理
    # =====================================================

    process_command(
        command
    )


# =========================================================
# メイン
# =========================================================

def main():

    print("")
    print("============================================================")
    print("🤖 めいな Voice Agent 起動完了")
    print("============================================================")

    print(
        "🧠 faster-whisper : large-v3"
    )

    print(
        "🧠 brain          : v3.6"
    )

    print(
        "🖥️ PC操作          : ON"
    )

    print(
        "🔊 音声出力         : ON"
    )

    print("")

    print(
        "🎤 「メイナ」と呼びかけてください"
    )

    print(
        "🎤 例：「メイナ、電卓を開いて」"
    )

    print(
        "🎤 例：「メイナ、メモ帳を開いて」"
    )

    print(
        "🎤 例：「メイナ、Discordを開いて」"
    )

    print(
        "🎤 例：「メイナ、VALORANTを開いて」"
    )

    print("")

    print(
        "終了する場合は Ctrl+C"
    )

    print("============================================================")
    print("")

    # =====================================================
    # 起動音声
    # =====================================================

    speak(
        "めいな、起動しました"
    )

    # =====================================================
    # 待機ループ
    # =====================================================

    while True:

        try:

            print("")
            print(
                "💤 待機中... 「メイナ」と呼んでください"
            )

            # -------------------------------------------------
            # ウェイクワード待機
            #
            # 5秒にして長い一文の取りこぼしを減らす
            # -------------------------------------------------

            # 一息で長い命令を言えるように待機録音を5秒にする
            text = listen(
                duration=5.0
            )

            if not text:

                continue

            # -------------------------------------------------
            # 音声処理
            # -------------------------------------------------

            handle_voice_input(
                text
            )

        except KeyboardInterrupt:

            print("")
            print(
                "🛑 めいなを終了します"
            )

            speak(
                "またね！"
            )

            break

        except SystemExit:

            print("")
            print(
                "🛑 めいなを終了します"
            )

            break

        except Exception as e:

            print("")
            print(
                "❌ メインループエラー:",
                e
            )

            try:

                speak(
                    "エラーが発生しました"
                )

            except Exception:
                pass

            time.sleep(
                1
            )


# =========================================================
# 起動
# =========================================================

if __name__ == "__main__":

    main()
