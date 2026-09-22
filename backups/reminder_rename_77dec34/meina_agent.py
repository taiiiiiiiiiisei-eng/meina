import re
import os
import time
import asyncio
import tempfile
import sysconfig
import shutil
import subprocess

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

# 実際に現在のPythonプロセスが使っているsite-packagesを最優先する。
# VS Codeのデバッガーや別の起動方法でも、Python本体とCUDA DLLの環境を一致させる。
active_site_packages = sysconfig.get_paths().get("purelib", "")
fallback_site_packages = [
    os.path.join(BASE_DIR, ".venv", "Lib", "site-packages"),
    os.path.join(os.path.dirname(BASE_DIR), ".venv", "Lib", "site-packages"),
]

SITE_PACKAGES = active_site_packages if os.path.exists(active_site_packages) else None

if SITE_PACKAGES is None:
    for path in fallback_site_packages:
        if os.path.exists(path):
            SITE_PACKAGES = path
            break

if SITE_PACKAGES is None:
    SITE_PACKAGES = fallback_site_packages[-1]


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

# Neural TTSを優先し、利用できない場合はWindows TTSへ自動フォールバック。
# 声は環境変数で切り替え可能。起動時に現在の声を表示する。
NEURAL_TTS_VOICE = os.environ.get("MEINA_NEURAL_VOICE", "ja-JP-NanamiNeural")
MEINA_VOICE_PRESETS = {
    "nanami": "ja-JP-NanamiNeural",
    "nanami_neural": "ja-JP-NanamiNeural",
    "keita": "ja-JP-KeitaNeural",
    "shiori": "ja-JP-ShioriNeural",
}
MEINA_VOICE_PRESET = os.environ.get("MEINA_VOICE_PRESET", "").strip().lower()
if MEINA_VOICE_PRESET in MEINA_VOICE_PRESETS:
    NEURAL_TTS_VOICE = MEINA_VOICE_PRESETS[MEINA_VOICE_PRESET]
print("🔊 めいな Neural Voice:", NEURAL_TTS_VOICE)
MEINA_TTS_RATE = int(os.environ.get("MEINA_TTS_RATE", "158"))
MEINA_TTS_VOLUME = float(os.environ.get("MEINA_TTS_VOLUME", "1.0"))
MEINA_NEURAL_RATE = os.environ.get("MEINA_NEURAL_RATE", "-8%")
MEINA_VOICE_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "meina_voice_settings.json")

def load_meina_voice_settings():
    global NEURAL_TTS_VOICE, MEINA_NEURAL_RATE, MEINA_TTS_VOLUME
    try:
        import json
        if not os.path.exists(MEINA_VOICE_SETTINGS_FILE):
            return
        with open(MEINA_VOICE_SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        voice = settings.get("voice")
        rate = settings.get("rate")
        volume = settings.get("volume")
        if voice in MEINA_VOICE_PRESETS.values():
            NEURAL_TTS_VOICE = voice
        if isinstance(rate, str):
            MEINA_NEURAL_RATE = rate
        if isinstance(volume, (int, float)):
            MEINA_TTS_VOLUME = max(0.2, min(1.0, float(volume)))
    except Exception as e:
        print("⚠️ 音声設定の読み込みをスキップ:", e)

def save_meina_voice_settings():
    try:
        import json
        settings = {
            "voice": NEURAL_TTS_VOICE,
            "rate": MEINA_NEURAL_RATE,
            "volume": MEINA_TTS_VOLUME,
        }
        with open(MEINA_VOICE_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠️ 音声設定の保存をスキップ:", e)


try:
    import edge_tts
    import pygame
    NEURAL_TTS_AVAILABLE = True
    print("🔊 Neural TTS: ON")
    print("🔊 Neural Voice:", NEURAL_TTS_VOICE)
except Exception:
    NEURAL_TTS_AVAILABLE = False
    print("🔊 Neural TTS: OFF（Windows TTSを使用）")

engine = pyttsx3.init()
_ENGINE_RATE_PRESETS = {"-18%": 140, "-8%": 158, "+8%": 176}
engine.setProperty("rate", MEINA_TTS_RATE)
engine.setProperty("volume", max(0.0, min(1.0, MEINA_TTS_VOLUME)))
load_meina_voice_settings()
engine.setProperty("rate", _ENGINE_RATE_PRESETS.get(MEINA_NEURAL_RATE, MEINA_TTS_RATE))
engine.setProperty("volume", MEINA_TTS_VOLUME)

MEINA_VOICE = os.environ.get("MEINA_VOICE", "Ayumi").strip().lower()

try:
    voices = engine.getProperty("voices")
    selected_voice = None
    japanese_voices = []
    for voice in voices:
        name = str(voice.name)
        name_lower = name.lower()
        languages = str(getattr(voice, "languages", "")).lower()
        if (
            "japanese" in name_lower
            or "日本語" in name
            or "haruka" in name_lower
            or "ayumi" in name_lower
            or "ichiro" in name_lower
            or "ja-jp" in languages
        ):
            japanese_voices.append(voice)
        if MEINA_VOICE and MEINA_VOICE in name_lower:
            selected_voice = voice
    if selected_voice is None and japanese_voices:
        selected_voice = next((v for v in japanese_voices if "haruka" in str(v.name).lower()), japanese_voices[0])
    if selected_voice is not None:
        engine.setProperty("voice", selected_voice.id)
        print("🔊 Windows TTS:", selected_voice.name)
    else:
        print("⚠️ 日本語音声が見つかりませんでした")
except Exception as e:
    print("⚠️ 音声設定エラー:", e)

def _prepare_tts_text(text):
    """AIの返答を読み上げ向けに軽く整える。"""
    text = str(text or "").strip()
    if not text:
        return ""
    for src, dst in (("```", ""), ("**", ""), ("__", ""), ("###", ""), ("##", ""), ("#", ""), ("・", "、")):
        text = text.replace(src, dst)
    import re
    text = re.sub(r"https?://\S+", "リンク", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def set_meina_voice(preset):
    """Neural Voiceのプリセットを変更する。"""
    global NEURAL_TTS_VOICE
    key = str(preset or "").strip().lower()
    if key not in MEINA_VOICE_PRESETS:
        return False
    NEURAL_TTS_VOICE = MEINA_VOICE_PRESETS[key]
    save_meina_voice_settings()
    print("🔊 めいなの声を変更:", NEURAL_TTS_VOICE)
    return True


def set_meina_volume(direction):
    global MEINA_TTS_VOLUME
    if direction == "up":
        MEINA_TTS_VOLUME = min(1.0, MEINA_TTS_VOLUME + 0.1)
    elif direction == "down":
        MEINA_TTS_VOLUME = max(0.2, MEINA_TTS_VOLUME - 0.1)
    else:
        return False
    engine.setProperty("volume", MEINA_TTS_VOLUME)
    save_meina_voice_settings()
    return True


def set_meina_rate(preset):
    global MEINA_NEURAL_RATE
    rates = {"slow": "-18%", "normal": "-8%", "fast": "+8%"}
    if preset not in rates:
        return False
    MEINA_NEURAL_RATE = rates[preset]
    engine.setProperty("rate", _ENGINE_RATE_PRESETS.get(MEINA_NEURAL_RATE, MEINA_TTS_RATE))
    save_meina_voice_settings()
    return True


def _speak_neural(text):
    """Neural TTSで音声を生成して再生する。"""
    async def generate(path):
        neural_volume = f"{round((MEINA_TTS_VOLUME - 1.0) * 100):+d}%"
        communicate = edge_tts.Communicate(text, NEURAL_TTS_VOICE, rate=MEINA_NEURAL_RATE, volume=neural_volume, pitch="-2Hz")
        await communicate.save(path)
    fd, path = tempfile.mkstemp(suffix=".mp3", prefix="meina_tts_")
    os.close(fd)
    try:
        asyncio.run(generate(path))
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.03)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

def speak(text):
    """めいなの自然な音声出力。Neural TTS優先、失敗時はWindows TTS。"""
    speech = _prepare_tts_text(text)
    if not speech:
        return
    print("🔊 めいな:", text)
    if NEURAL_TTS_AVAILABLE:
        try:
            _speak_neural(speech)
            return
        except Exception as e:
            print("⚠️ Neural TTSエラー。Windows TTSへ切り替えます:", e)
    try:
        engine.stop()
        engine.say(speech)
        engine.runAndWait()
    except Exception as e:
        print("❌ TTS ERROR:", e)
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
# =========================================================
# 軽量な音声前処理
# =========================================================
from meina_voice_intent import (
    WAKE_WORDS,
    contains_wake_word,
    correct_recognition,
    is_invalid_command,
    normalize_text,
    remove_wake_word,
    listen_command_with_retry,
)


# PC操作
# =========================================================

def _format_reminders(items):
    if not items:
        return "予定はありません。"
    lines = []
    for item in items:
        due = str(item.get("due_at", "")).replace("T", " ")
        status = "完了" if item.get("done") else "未完了"
        lines.append(f"・{item.get('text', '')} / {due} / {status}")
    return "\n".join(lines)


def _execute_routed_command_base(route):
    """command_router が許可した固定コマンドだけを実行する。"""
    kind = route["kind"]
    target = route.get("target")
    query = route.get("query")

    try:
        if kind == "help":
            result = (
                "めいなは、会話、天気、現在時刻、PC状態、リマインダー、"
                "Google・YouTube検索、アプリ起動、配信準備、Twitch切り抜き、Twitch投稿準備、配信中の見どころ監視・見どころ一覧・AIおすすめ選定に対応しています。"
            )
        elif kind == "self_status":
            neural = "OK" if NEURAL_TTS_AVAILABLE else "OFF"
            cuda = "OK" if os.path.isdir(CUBLAS_BIN) and os.path.isdir(CUDNN_BIN) else "WARN"
            nvidia = "OK" if shutil.which("nvidia-smi") else "WARN"
            ollama_status = "WARN"
            ollama_model = "WARN"
            try:
                proc = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                    encoding="utf-8",
                    errors="replace",
                )
                if proc.returncode == 0:
                    ollama_status = "OK"
                    ollama_model = "OK" if "meina" in (proc.stdout or "").lower() else "WARN"
            except Exception:
                pass
            result = (
                "めいなの自己診断です。"
                f"Whisperは{'OK' if whisper_model else 'NG'}、"
                f"brain_coreは{'OK' if brain_core else 'NG'}、"
                f"Ollamaサービスは{ollama_status}、"
                f"meinaモデルは{ollama_model}、"
                f"CUDA DLLは{cuda}、"
                f"NVIDIAドライバーは{nvidia}、"
                f"Neural TTSは{neural}、"
                f"Windows TTSは{'OK' if engine else 'NG'}です。"
            )
        elif kind == "weather":
            result = tools.get_weather(
                None if target == "current" else target,
                mode=query or "today",
            )
        elif kind == "date":
            result = tools.get_date()
        elif kind == "time":
            result = tools.get_time()
        elif kind == "weekday":
            result = tools.get_weekday()
        elif kind == "pc_status":
            from meina_pc_status import format_pc_status, get_pc_status
            result = format_pc_status(get_pc_status())
        elif kind == "reminder":
            from meina_reminder_parser import parse_reminder_command
            from meina_reminders import add_reminder
            parsed = parse_reminder_command(query or "")
            if not parsed:
                result = "予定の日時を読み取れませんでした。例えば「30分後に宿題をする予定を追加して」と言ってください。"
            else:
                item = add_reminder(parsed["text"], parsed["due_at"])
                result = f"予定を追加しました。「{item['text']}」は{item['due_at'].replace('T', ' ')}です。"
        elif kind == "reminder_today":
            from meina_reminders import today_reminders
            items = today_reminders()
            result = "今日の予定はありません。" if not items else "今日の予定です。\n" + _format_reminders(items)
        elif kind == "reminder_tomorrow":
            from meina_reminders import tomorrow_reminders
            items = tomorrow_reminders()
            result = "明日の予定はありません。" if not items else "明日の予定です。\n" + _format_reminders(items)
        elif kind == "reminder_upcoming":
            from meina_reminders import upcoming_reminders
            items = upcoming_reminders()
            result = "今後の予定はありません。" if not items else "今後の予定です。\n" + _format_reminders(items)
        elif kind == "reminder_list":
            from meina_reminders import list_reminders
            items = list_reminders()
            result = "未完了のリマインダーはありません。" if not items else "未完了のリマインダーです。\n" + _format_reminders(items)
        elif kind == "reminder_reschedule":
            from meina_reminders import find_reminders, reschedule_reminder

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            due_at = str(request.get("due_at") or "").strip()

            if not query_text:
                result = "変更する予定名を指定してください。"
            elif not due_at:
                result = "変更後の日時を指定してください。"
            else:
                matches = find_reminders(query_text)
                if not matches:
                    result = "変更する予定が見つかりませんでした。"
                elif len(matches) > 1:
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        "もう少し具体的に指定してください。"
                    )
                else:
                    item = reschedule_reminder(matches[0]["id"], due_at)
                    if item:
                        result = (
                            f"「{item['text']}」の日時を"
                            f"{item['due_at'].replace('T', ' ')}に変更しました。"
                        )
                    else:
                        result = f"「{query_text}」の日時を変更できませんでした。"
        elif kind in ("reminder_done", "reminder_delete"):
            from meina_reminders import complete_reminder, delete_reminder, find_reminders
            query_text = re.sub(
                r"(リマインダー|リマインド)(を)?(完了|削除)(して|してください|お願い(?:します)?)?",
                "",
                query or "",
            ).strip(" 、。！？?")
            if not query_text:
                result = "対象のリマインダー名を指定してください。"
            else:
                matches = find_reminders(query_text)
                if not matches:
                    result = "対象のリマインダーが見つかりませんでした。"
                elif len(matches) > 1:
                    result = f"「{query_text}」に一致するリマインダーが{len(matches)}件あります。もう少し具体的に指定してください。"
                else:
                    item = matches[0]
                    ok = complete_reminder(item["id"]) if kind == "reminder_done" else delete_reminder(item["id"])
                    action = "完了" if kind == "reminder_done" else "削除"
                    result = f"「{item['text']}」を{action}しました。" if ok else f"「{item['text']}」を{action}できませんでした。"
        elif kind == "twitch_live_highlight":
            from twitch_live_highlight import is_monitor_running, start_monitor
            if is_monitor_running():
                result = "配信中の見どころ監視はすでに起動しています。"
            elif start_monitor():
                result = "配信中の見どころ監視を開始しました。別ウィンドウで動作します。"
            else:
                result = "配信中の見どころ監視を開始できませんでした。"
        elif kind == "twitch_live_highlight_stop":
            from twitch_live_highlight import stop_monitor
            result = (
                "配信中の見どころ監視を停止しました。"
                if stop_monitor()
                else "起動中の配信中見どころ監視は見つかりませんでした。"
            )
        elif kind == "twitch_live_highlight_list":
            from twitch_live_highlight import format_candidates, load_candidates
            candidates = load_candidates(limit=5)
            result = format_candidates(candidates)
        elif kind == "twitch_live_highlight_shortlist":
            from twitch_live_highlight import format_shortlist, shortlist_candidates
            candidates = shortlist_candidates(limit=3)
            result = format_shortlist(candidates)
        elif kind == "twitch_shortlist_clip":
            from meina_twitch import run_shortlist_twitch_command
            clip_result = run_shortlist_twitch_command(max_clips=3)
            result = clip_result.get("message", "AIおすすめ候補から切り抜きを作成できませんでした。")
        elif kind == "twitch_publish_prep":
            from twitch_publish_queue import prepare_publish_queue
            queue_result = prepare_publish_queue()
            result = queue_result.get("message", "Twitchの投稿準備を作成できませんでした。")
        elif kind == "twitch_clip":
            from meina_twitch import run_twitch_clip_command
            clip_result = run_twitch_clip_command(query or "")
            result = clip_result.get("message", "Twitchの切り抜きを処理できませんでした。")
        elif kind == "app_open":
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
                "browser": tools.open_browser,
            }
            result = web_functions[target]()
        elif kind == "web_search":
            search_functions = {
                "google": tools.google_search,
                "youtube": tools.youtube_search,
                "browser": tools.google_search,
            }
            result = search_functions[target](query)
        else:
            return False

        print("🛡️ 許可済みPC操作:", route)
        speak(result)
        return result

    except Exception as e:
        print("❌ PC操作エラー:", e)
        speak("PC操作を実行できませんでした")
        return True


MEINA_UPGRADE_TASK_PLAN_LOCAL_V1_EXEC

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
    if route.get("kind") == "voice_change":
        if set_meina_voice(route.get("target")):
            labels = {"nanami": "ナナミ", "keita": "ケイタ", "shiori": "シオリ"}
            message = f"{labels.get(route.get('target'), 'この声')}に変更しました"
        else:
            message = "その声には変更できませんでした"
        speak(message)
        return message
    if route.get("kind") == "voice_rate":
        if set_meina_rate(route.get("target")):
            labels = {"slow": "ゆっくり", "normal": "標準", "fast": "速め"}
            message = f"話す速さを{labels.get(route.get('target'), '変更')}にしました"
        else:
            message = "話す速さを変更できませんでした"
        speak(message)
        return message
    if route.get("kind") == "voice_volume":
        if set_meina_volume(route.get("target")):
            message = "声の音量を調整しました"
        else:
            message = "声の音量を調整できませんでした"
        speak(message)
        return message
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

MEINA_CHAT_HISTORY = []
MEINA_CHAT_HISTORY_LIMIT = 8
MEINA_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "meina_memory.json")
MEINA_MEMORY_MAX_ITEMS = 30

def load_meina_memory():
    try:
        import json
        if not os.path.exists(MEINA_MEMORY_FILE):
            return []
        with open(MEINA_MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict) and isinstance(item.get("content"), str)][-MEINA_MEMORY_MAX_ITEMS:]
    except Exception as e:
        print("⚠️ 長期記憶の読み込みをスキップ:", e)
        return []

def save_meina_memory(memory):
    try:
        import json
        with open(MEINA_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory[-MEINA_MEMORY_MAX_ITEMS:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠️ 長期記憶の保存をスキップ:", e)

MEINA_MEMORY = load_meina_memory()


def chat_with_meina(text):
    """
    普通の質問をOllamaのめいなへ送る。
    直近の会話だけを短く保持する。
    """

    if not text:
        return ""

    try:
        MEINA_CHAT_HISTORY.append({
            "role": "user",
            "content": text,
        })
        messages = MEINA_CHAT_HISTORY[-MEINA_CHAT_HISTORY_LIMIT:]

        if MEINA_MEMORY:
            memory_text = "\n".join(
                "- " + str(item.get("content", "")).strip()
                for item in MEINA_MEMORY
                if str(item.get("content", "")).strip()
            )
            if memory_text:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "以下はユーザーが明示的に覚えてほしいと指定した情報です。"
                            "回答に関係する場合だけ参考にしてください。"
                            "記憶にない情報を推測して補わないでください。\n"
                            + memory_text
                        ),
                    }
                ] + messages

        response = ollama.chat(
            model="meina",
            messages=messages
        )

        answer = response["message"]["content"].strip()

        if not answer:
            answer = "すみません、うまく答えられませんでした。"

        MEINA_CHAT_HISTORY.append({
            "role": "assistant",
            "content": answer,
        })
        del MEINA_CHAT_HISTORY[:-MEINA_CHAT_HISTORY_LIMIT]

        if any(p in text for p in ("覚えて", "記憶して", "覚えといて", "忘れないで")):
            MEINA_MEMORY.append({
                "role": "user",
                "content": text,
            })
            save_meina_memory(MEINA_MEMORY)

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

    if route is not None:

        # ルートが存在する命令は、実行結果が空文字でも
        # 通常会話へフォールバックしない。
        # これにより「天気を教えて」などの固定コマンドが
        # 意図せず Ollama 会話へ流れるのを防ぐ。
        return execute_routed_command(route)

    # =====================================================
    # 普通の会話
    # =====================================================

    return chat_with_meina(
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

        command = listen_command_with_retry(
            listen,
            attempts=2,
            duration=5.0,
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
