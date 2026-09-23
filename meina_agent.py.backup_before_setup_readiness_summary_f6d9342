import re
import os
import time
import asyncio
import tempfile
import sysconfig
import shutil
import subprocess
import threading

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
_SPEAK_LOCK = threading.RLock()

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
    """めいなの自然な音声出力。複数スレッドのTTS呼び出しを直列化する。"""
    speech = _prepare_tts_text(text)
    if not speech:
        return

    with _SPEAK_LOCK:
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
    from meina_reminders import (
        format_reminder_category,
        format_reminder_due,
        format_reminder_duration,
        format_reminder_location,
        format_reminder_note,
        format_reminder_importance,
        format_reminder_repeat,
    )

    lines = []
    for item in items:
        due = format_reminder_due(item.get("due_at", ""))
        repeat = format_reminder_repeat(item)
        duration = format_reminder_duration(item)
        importance = format_reminder_importance(item)
        category = format_reminder_category(item)
        location = format_reminder_location(item)
        note = format_reminder_note(item)
        if item.get("done"):
            status = "完了"
        elif item.get("paused"):
            status = "一時停止中"
        else:
            status = "未完了"
        repeat_text = f"、{repeat}" if repeat else ""
        duration_text = f"、所要{duration}" if duration else ""
        importance_text = "、重要" if importance else ""
        category_text = f"、カテゴリ:{category}" if category else ""
        location_text = f"、場所:{location}" if location else ""
        note_text = "、メモあり" if note else ""
        try:
            pre_minutes = int(item.get("notify_before_minutes") or 0)
        except (TypeError, ValueError):
            pre_minutes = 0
        pre_text = f"、{pre_minutes}分前通知" if pre_minutes > 0 else ""
        lines.append(
            f"・{item.get('text', '')}、{due}{duration_text}{repeat_text}{importance_text}{category_text}{location_text}{note_text}{pre_text}、{status}"
        )
    return "\n".join(lines)


def _format_minutes(minutes):
    """分数を読み上げやすい時間表現へ変換する。"""
    try:
        value = max(0, int(minutes))
    except (TypeError, ValueError):
        value = 0
    hours, remain = divmod(value, 60)
    if hours and remain:
        return f"{hours}時間{remain}分"
    if hours:
        return f"{hours}時間"
    return f"{remain}分"


def _format_completion_events(events):
    if not events:
        return "完了履歴はありません。"

    from meina_reminders import (
        format_reminder_due,
        format_reminder_duration,
        format_reminder_location,
        format_reminder_note,
    )

    lines = []
    for event in events:
        completed = format_reminder_due(event.get("completed_at", ""))
        due = format_reminder_due(event.get("due_at", ""))
        duration = format_reminder_duration(event)
        duration_text = f"、所要{duration}" if duration else ""
        note = format_reminder_note(event)
        note_text = "、メモあり" if note else ""
        location = format_reminder_location(event)
        location_text = f"、場所:{location}" if location else ""
        category = str(event.get("category") or "").strip()
        category_text = f"、カテゴリ:{category}" if category else ""
        important_text = "、重要" if event.get("important") else ""
        lines.append(
            f"・{event.get('text', '')}、完了:{completed}、予定:{due}"
            f"{duration_text}{category_text}{location_text}{important_text}{note_text}"
        )
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
                "毎日・平日・毎週・毎月の繰り返し予定、Google・YouTube検索、"
                "アプリ起動、配信準備、Twitch切り抜き、Twitch投稿準備、"
                "配信中の見どころ監視・見どころ一覧・AIおすすめ選定に対応しています。"
            )
        elif kind == "self_status":
            from meina_reminder_worker import is_reminder_worker_running

            neural = "OK" if NEURAL_TTS_AVAILABLE else "OFF"
            reminder_worker = "OK" if is_reminder_worker_running() else "WARN"
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
                f"リマインダー監視は{reminder_worker}、"
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
            from meina_reminders import (
                add_reminder,
                find_conflicting_reminders,
                find_duplicate_reminder,
                format_reminder_due,
                format_reminder_duration,
                format_reminder_repeat,
            )
            parsed = parse_reminder_command(query or "")
            if not parsed:
                result = (
                    "予定の日時を読み取れませんでした。例えば"
                    "「30分後に宿題をする予定を追加して」や"
                    "「毎日18時に薬をリマインドして」と言ってください。"
                )
            else:
                duplicate = find_duplicate_reminder(
                    parsed["text"],
                    parsed["due_at"],
                    repeat_rule=parsed.get("repeat_rule"),
                    repeat_day=parsed.get("repeat_day"),
                    duration_minutes=parsed.get("duration_minutes"),
                )
                if duplicate:
                    repeat = format_reminder_repeat(duplicate)
                    duration = format_reminder_duration(duplicate)
                    repeat_text = f"、{repeat}" if repeat else ""
                    duration_text = f"、所要{duration}" if duration else ""
                    result = (
                        f"同じ予定がすでにあります。「{duplicate['text']}」は"
                        f"{format_reminder_due(duplicate['due_at'])}"
                        f"{duration_text}{repeat_text}です。"
                    )
                else:
                    item = add_reminder(
                        parsed["text"],
                        parsed["due_at"],
                        repeat_rule=parsed.get("repeat_rule"),
                        repeat_day=parsed.get("repeat_day"),
                        duration_minutes=parsed.get("duration_minutes"),
                    )
                    repeat = format_reminder_repeat(item)
                    duration = format_reminder_duration(item)
                    repeat_text = f"、{repeat}" if repeat else ""
                    duration_text = f"、所要{duration}" if duration else ""
                    result = (
                        f"予定を追加しました。「{item['text']}」は"
                        f"{format_reminder_due(item['due_at'])}"
                        f"{duration_text}{repeat_text}です。"
                    )
                    overlaps = find_conflicting_reminders(item["id"])
                    if overlaps:
                        names = "、".join(
                            f"「{other.get('text', '')}」"
                            for other in overlaps[:3]
                        )
                        result += (
                            f" ただし、{names}と時間が重なっています。"
                        )
        elif kind == "reminder_conflicts":
            from meina_reminders import (
                find_schedule_conflicts,
                format_reminder_due,
                format_reminder_duration,
            )

            try:
                days = max(1, min(int(query or 7), 31))
            except (TypeError, ValueError):
                days = 7
            conflicts = find_schedule_conflicts(days=days)
            if not conflicts:
                result = f"今後{days}日以内に重なっている予定はありません。"
            else:
                lines = []
                for first, second in conflicts[:5]:
                    first_duration = format_reminder_duration(first) or "時刻のみ"
                    second_duration = format_reminder_duration(second) or "時刻のみ"
                    lines.append(
                        f"・「{first['text']}」"
                        f"（{format_reminder_due(first['due_at'])}、{first_duration}）と"
                        f"「{second['text']}」"
                        f"（{format_reminder_due(second['due_at'])}、{second_duration}）"
                    )
                result = (
                    f"重なっている予定が{len(conflicts)}組あります。\n"
                    + "\n".join(lines)
                )
        elif kind == "reminder_schedule_free":
            from datetime import datetime, timedelta
            from meina_reminders import (
                add_reminder,
                find_first_free_slot,
                format_reminder_due,
                format_reminder_duration,
            )

            request = query if isinstance(query, dict) else {}
            current = datetime.now().astimezone()
            day_offset = 1 if request.get("day") == "明日" else 0
            target_date = (current + timedelta(days=day_offset)).date()
            try:
                required = int(request.get("duration_minutes"))
                start_at = current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=int(request.get("start_hour", 0)),
                    minute=int(request.get("start_minute", 0)),
                    second=0,
                    microsecond=0,
                )
                end_at = current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=int(request.get("end_hour", 0)),
                    minute=int(request.get("end_minute", 0)),
                    second=0,
                    microsecond=0,
                )
            except (TypeError, ValueError):
                result = "空き時間へ入れる予定の条件を読み取れませんでした。"
            else:
                if day_offset == 0 and start_at < current:
                    start_at = current.replace(second=0, microsecond=0)
                    if start_at < current:
                        start_at += timedelta(minutes=1)

                slot = (
                    find_first_free_slot(
                        start_at,
                        end_at,
                        required_minutes=required,
                    )
                    if start_at < end_at
                    else None
                )
                if slot is None:
                    result = "指定した時間帯に必要な長さの空き時間がありません。"
                else:
                    slot_start, _ = slot
                    item = add_reminder(
                        str(request.get("text") or "").strip(),
                        slot_start.isoformat(timespec="seconds"),
                        duration_minutes=required,
                    )
                    result = (
                        f"空いている時間に「{item['text']}」を追加しました。"
                        f"{format_reminder_due(item['due_at'])}から"
                        f"{format_reminder_duration(item)}です。"
                    )
        elif kind == "reminder_free_total":
            from datetime import datetime, timedelta
            from meina_reminders import schedule_window_stats

            request = query if isinstance(query, dict) else {}
            current = datetime.now().astimezone()
            day_offset = 1 if request.get("day") == "明日" else 0
            target_date = (current + timedelta(days=day_offset)).date()
            try:
                start_at = current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=int(request.get("start_hour", 0)),
                    minute=int(request.get("start_minute", 0)),
                    second=0,
                    microsecond=0,
                )
                end_at = current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=int(request.get("end_hour", 0)),
                    minute=int(request.get("end_minute", 0)),
                    second=0,
                    microsecond=0,
                )
            except (TypeError, ValueError):
                result = "空き時間の範囲を読み取れませんでした。"
            else:
                if day_offset == 0 and start_at < current:
                    start_at = current.replace(second=0, microsecond=0)
                    if start_at < current:
                        start_at += timedelta(minutes=1)

                if start_at >= end_at:
                    result = "指定した時間帯はすでに終了しています。"
                else:
                    stats = schedule_window_stats(start_at, end_at)
                    result = (
                        f"指定した時間帯は全部で"
                        f"{_format_minutes(stats['window_minutes'])}です。"
                        f"空きは{_format_minutes(stats['free_minutes'])}、"
                        f"予定で埋まっているのは"
                        f"{_format_minutes(stats['busy_minutes'])}です。"
                    )
                    if stats["longest_free_minutes"] > 0:
                        result += (
                            "最長の連続した空きは"
                            f"{_format_minutes(stats['longest_free_minutes'])}です。"
                        )
        elif kind == "reminder_focus_slot":
            from datetime import datetime, timedelta
            from meina_reminders import find_first_free_slot

            request = query if isinstance(query, dict) else {}
            current = datetime.now().astimezone()
            day_offset = 1 if request.get("day") == "明日" else 0
            target_date = (current + timedelta(days=day_offset)).date()

            try:
                required = max(
                    1,
                    min(int(request.get("duration_minutes", 60)), 1440),
                )
            except (TypeError, ValueError):
                required = 60

            if day_offset == 0:
                start_at = current.replace(second=0, microsecond=0)
                if start_at < current:
                    start_at += timedelta(minutes=1)
            else:
                start_at = current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

            end_at = (
                current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                + timedelta(days=1)
            )

            slot = (
                find_first_free_slot(
                    start_at,
                    end_at,
                    required_minutes=required,
                )
                if start_at < end_at
                else None
            )

            if slot is None:
                result = (
                    f"{request.get('day') or '今日'}は"
                    f"{_format_minutes(required)}まとまって空いている時間が"
                    "見つかりませんでした。"
                )
            else:
                slot_start, slot_end = slot

                def _clock_text(value):
                    return (
                        f"{value.hour}時{value.minute}分"
                        if value.minute
                        else f"{value.hour}時"
                    )

                result = (
                    f"{request.get('day') or '今日'}の最初の"
                    f"{_format_minutes(required)}の集中候補は、"
                    f"{_clock_text(slot_start)}から"
                    f"{_clock_text(slot_end)}です。"
                )
        elif kind == "reminder_free_time":
            from datetime import datetime, timedelta
            from meina_reminders import find_free_time_slots

            request = query if isinstance(query, dict) else {}
            current = datetime.now().astimezone()
            day_offset = 1 if request.get("day") == "明日" else 0
            target_date = (current + timedelta(days=day_offset)).date()
            try:
                minimum_minutes = max(
                    1,
                    min(int(request.get("minimum_minutes", 15)), 1440),
                )
                start_at = current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=int(request.get("start_hour", 0)),
                    minute=int(request.get("start_minute", 0)),
                    second=0,
                    microsecond=0,
                )
                end_at = current.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day,
                    hour=int(request.get("end_hour", 0)),
                    minute=int(request.get("end_minute", 0)),
                    second=0,
                    microsecond=0,
                )
            except (TypeError, ValueError):
                result = "空き時間の範囲を読み取れませんでした。"
            else:
                if day_offset == 0 and start_at < current:
                    start_at = current.replace(second=0, microsecond=0)
                    if start_at < current:
                        start_at += timedelta(minutes=1)

                slots = (
                    find_free_time_slots(
                        start_at,
                        end_at,
                        minimum_minutes=minimum_minutes,
                    )
                    if start_at < end_at
                    else []
                )

                def _clock_text(value):
                    return (
                        f"{value.hour}時{value.minute}分"
                        if value.minute
                        else f"{value.hour}時"
                    )

                if not slots:
                    result = (
                        f"指定した時間帯に{minimum_minutes}分以上の"
                        "空き時間はありません。"
                    )
                else:
                    slot_text = "、".join(
                        f"{_clock_text(start)}から{_clock_text(end)}"
                        for start, end in slots
                    )
                    result = (
                        f"{minimum_minutes}分以上の空き時間は、"
                        f"{slot_text}です。"
                    )
        elif kind == "reminder_remaining_today":
            from datetime import datetime, timedelta
            from meina_reminders import (
                reminder_duration_summary,
                schedule_window_stats,
                today_reminders,
            )

            current = datetime.now().astimezone()
            start_at = current.replace(second=0, microsecond=0)
            if start_at < current:
                start_at += timedelta(minutes=1)
            end_at = (
                current.replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                + timedelta(days=1)
            )

            if start_at >= end_at:
                result = "今日は残り時間がありません。"
            else:
                stats = schedule_window_stats(start_at, end_at)
                today_summary = reminder_duration_summary(today_reminders())
                result = (
                    f"今日の残りは{_format_minutes(stats['window_minutes'])}です。"
                    f"空きは{_format_minutes(stats['free_minutes'])}、"
                    f"予定で埋まっているのは"
                    f"{_format_minutes(stats['busy_minutes'])}です。"
                )
                if stats["longest_free_minutes"]:
                    result += (
                        "最長の連続した空きは"
                        f"{_format_minutes(stats['longest_free_minutes'])}です。"
                    )
                if today_summary["missing_count"]:
                    result += (
                        f"所要時間未設定の予定が"
                        f"{today_summary['missing_count']}件あるため、"
                        "実際の空き時間はこれより少ない可能性があります。"
                    )
        elif kind == "reminder_day_load":
            from datetime import datetime, timedelta
            from meina_reminders import day_schedule_summary

            current = datetime.now().astimezone()
            is_tomorrow = str(query or "") == "tomorrow"
            target_date = (
                current.date() + timedelta(days=1)
                if is_tomorrow
                else current.date()
            )
            label = "明日" if is_tomorrow else "今日"
            summary = day_schedule_summary(target_date, current)

            if summary["count"] == 0:
                result = f"{label}の未完了予定はありません。"
            else:
                result = (
                    f"{label}の未完了予定は{summary['count']}件です。"
                )
                if summary["timed_count"]:
                    result += (
                        "所要時間設定済みは"
                        f"{summary['timed_count']}件で、合計"
                        f"{_format_minutes(summary['total_minutes'])}です。"
                    )
                if summary["important_count"]:
                    result += (
                        f"重要予定は{summary['important_count']}件あります。"
                    )
                if summary["conflict_pairs"]:
                    result += (
                        f"時間が重なる組み合わせが"
                        f"{summary['conflict_pairs']}組あります。"
                    )
                if summary["missing_count"]:
                    result += (
                        f"所要時間未設定が{summary['missing_count']}件あるため、"
                        "予定時間の合計は暫定です。"
                    )
        elif kind == "reminder_week_peak":
            from datetime import date, datetime
            from meina_reminders import remaining_week_schedule_summary

            current = datetime.now().astimezone()
            summaries = remaining_week_schedule_summary(current)
            active = [summary for summary in summaries if summary["count"] > 0]

            if not active:
                result = "今週これからの予定はありません。"
            else:
                mode = str(query or "count")
                weekdays = ("月", "火", "水", "木", "金", "土", "日")

                if mode == "duration":
                    max_value = max(
                        summary["total_minutes"]
                        for summary in active
                    )
                    if max_value > 0:
                        selected = [
                            summary
                            for summary in active
                            if summary["total_minutes"] == max_value
                        ]
                        label_text = (
                            "所要時間設定済みの予定で見ると、"
                            "今週これから最も予定時間が長いのは"
                        )
                        value_text = _format_minutes(max_value)
                    else:
                        max_count = max(summary["count"] for summary in active)
                        selected = [
                            summary
                            for summary in active
                            if summary["count"] == max_count
                        ]
                        label_text = (
                            "所要時間設定済みの予定がないため件数で見ると、"
                            "今週これから予定が最も多いのは"
                        )
                        value_text = f"{max_count}件"
                else:
                    max_count = max(summary["count"] for summary in active)
                    selected = [
                        summary
                        for summary in active
                        if summary["count"] == max_count
                    ]
                    label_text = "今週これから予定が最も多いのは"
                    value_text = f"{max_count}件"

                day_labels = []
                for summary in selected:
                    target = date.fromisoformat(summary["date"])
                    day_labels.append(
                        f"{target.month}月{target.day}日"
                        f"{weekdays[target.weekday()]}曜"
                    )
                result = (
                    label_text
                    + "、".join(day_labels)
                    + f"で{value_text}です。"
                )

                missing_total = sum(
                    summary["missing_count"]
                    for summary in active
                )
                if mode == "duration" and missing_total:
                    result += (
                        f"今週これから所要時間未設定が"
                        f"{missing_total}件あるため、時間比較は暫定です。"
                    )
        elif kind == "reminder_category_duration_summary":
            from meina_reminders import (
                reminder_group_duration_summary,
                remaining_scope_reminders,
            )

            requested_scope = str(query or "")
            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            elif requested_scope == "tomorrow":
                scope, label = "tomorrow", "明日"
            else:
                scope, label = "today", "今日"

            items = remaining_scope_reminders(scope=scope)
            summaries = reminder_group_duration_summary(
                items,
                group_by="category",
            )
            if not summaries:
                result = f"{label}のカテゴリ別予定時間に表示できる予定はありません。"
            else:
                parts = []
                for category, summary in summaries.items():
                    if summary["total_minutes"] > 0:
                        part = (
                            f"{category}は"
                            f"{_format_minutes(summary['total_minutes'])}"
                        )
                        if summary["missing_count"]:
                            part += f"、所要時間未設定{summary['missing_count']}件"
                    else:
                        part = (
                            f"{category}は所要時間未設定"
                            f"{summary['missing_count']}件"
                        )
                    parts.append(part)
                result = (
                    f"{label}のカテゴリ別予定時間は、"
                    + "。".join(parts)
                    + "です。"
                )
        elif kind == "reminder_location_duration_summary":
            from meina_reminders import (
                reminder_group_duration_summary,
                remaining_scope_reminders,
            )

            requested_scope = str(query or "")
            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            elif requested_scope == "tomorrow":
                scope, label = "tomorrow", "明日"
            else:
                scope, label = "today", "今日"

            items = remaining_scope_reminders(scope=scope)
            summaries = reminder_group_duration_summary(
                items,
                group_by="location",
            )
            if not summaries:
                result = f"{label}の場所別予定時間に表示できる予定はありません。"
            else:
                parts = []
                for location, summary in summaries.items():
                    if summary["total_minutes"] > 0:
                        part = (
                            f"{location}は"
                            f"{_format_minutes(summary['total_minutes'])}"
                        )
                        if summary["missing_count"]:
                            part += f"、所要時間未設定{summary['missing_count']}件"
                    else:
                        part = (
                            f"{location}は所要時間未設定"
                            f"{summary['missing_count']}件"
                        )
                    parts.append(part)
                result = (
                    f"{label}の場所別予定時間は、"
                    + "。".join(parts)
                    + "です。"
                )
        elif kind == "reminder_duration_total":
            from meina_reminders import (
                filter_reminders_by_metadata,
                reminder_duration_summary,
                remaining_scope_reminders,
            )

            request = query if isinstance(query, dict) else {
                "scope": str(query or "today")
            }
            requested_scope = str(request.get("scope") or "today")
            category = str(request.get("category") or "").strip() or None
            location = str(request.get("location") or "").strip() or None

            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            elif requested_scope == "tomorrow":
                scope, label = "tomorrow", "明日"
            else:
                scope, label = "today", "今日"

            items = remaining_scope_reminders(scope=scope)
            if category or location:
                items = filter_reminders_by_metadata(
                    items,
                    category=category,
                    location=location,
                )
            summary = reminder_duration_summary(items)

            filter_text = ""
            if category:
                filter_text += f"「{category}」カテゴリの"
            if location:
                filter_text += f"場所が「{location}」の"
            subject = f"{label}の{filter_text}予定"

            if not items:
                result = f"{subject}はありません。"
            elif summary["timed_count"] == 0:
                result = (
                    f"{subject}は{len(items)}件ありますが、"
                    "所要時間が設定されている予定はありません。"
                )
            else:
                result = (
                    f"{subject}は所要時間が設定されている予定が"
                    f"{summary['timed_count']}件あり、合計"
                    f"{_format_minutes(summary['total_minutes'])}です。"
                )
                if summary["missing_count"]:
                    result += (
                        f"所要時間未設定の予定が"
                        f"{summary['missing_count']}件あります。"
                    )
        elif kind == "reminder_missing_duration":
            from meina_reminders import (
                remaining_scope_reminders,
                reminders_missing_duration,
            )

            requested_scope = str(query or "").strip()
            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            if requested_scope in scope_labels:
                source = remaining_scope_reminders(scope=requested_scope)
                items = reminders_missing_duration(source)
                label = scope_labels[requested_scope]
                empty_text = f"{label}は所要時間未設定の予定はありません。"
                count_text = (
                    f"{label}の所要時間未設定の予定が{len(items)}件あります。\n"
                )
            else:
                items = reminders_missing_duration()
                empty_text = "所要時間が未設定の予定はありません。"
                count_text = f"所要時間が未設定の予定が{len(items)}件あります。\n"

            result = (
                empty_text
                if not items
                else count_text + _format_reminders(items)
            )
        elif kind == "reminder_next_action":
            from datetime import datetime
            from meina_reminders import (
                format_reminder_due,
                format_reminder_duration,
                next_priority_reminder,
            )

            current = datetime.now().astimezone()
            item = next_priority_reminder(current)
            if not item:
                result = "優先候補にできる未完了予定はありません。"
            else:
                try:
                    due = datetime.fromisoformat(str(item.get("due_at", "")))
                    if due.tzinfo is None and current.tzinfo is not None:
                        due = due.replace(tzinfo=current.tzinfo)
                    elif due.tzinfo is not None and current.tzinfo is not None:
                        due = due.astimezone(current.tzinfo)
                    overdue = due < current
                except (TypeError, ValueError):
                    overdue = False

                if overdue and item.get("important"):
                    reason = "期限を過ぎていて、重要設定も付いています"
                elif overdue:
                    reason = "期限を過ぎています"
                elif item.get("important"):
                    reason = "重要設定が付いています"
                else:
                    reason = "次に近い予定です"

                duration = format_reminder_duration(item)
                duration_text = f"、所要{duration}" if duration else ""
                result = (
                    f"次の優先候補は「{item['text']}」です。"
                    f"{format_reminder_due(item.get('due_at', ''))}"
                    f"{duration_text}。{reason}。"
                )
        elif kind == "reminder_priority_today":
            from datetime import datetime
            from meina_reminders import prioritized_reminders

            current = datetime.now().astimezone()
            items = prioritized_reminders(
                current,
                target_date=current.date(),
            )
            if not items:
                result = "今日の優先候補にできる予定はありません。"
            else:
                top_items = items[:5]
                result = (
                    "今日の優先候補です。"
                    "期限切れ、重要設定、時刻の順で並べています。\n"
                    + _format_reminders(top_items)
                )
                if len(items) > len(top_items):
                    result += (
                        f"\nほかに{len(items) - len(top_items)}件あります。"
                    )
        elif kind == "reminder_brief":
            from meina_reminders import (
                completion_progress_summary,
                format_reminder_due,
                next_reminder,
                overdue_reminders,
                reminder_duration_summary,
                today_reminders,
            )

            items = today_reminders()
            active = [item for item in items if not item.get("paused")]
            paused = [item for item in items if item.get("paused")]
            important = [item for item in items if item.get("important")]
            next_item = next_reminder()
            overdue = overdue_reminders()
            duration_summary = reminder_duration_summary(items)
            completion_summary = completion_progress_summary(scope="today")

            if not items:
                result = "今日の予定はありません。"
            else:
                parts = [f"今日は予定が{len(items)}件あります。"]
                if active:
                    parts.append(f"通知中は{len(active)}件です。")
                if paused:
                    parts.append(f"一時停止中が{len(paused)}件あります。")
                if important:
                    parts.append(f"重要予定が{len(important)}件あります。")
                if completion_summary["completed_count"]:
                    parts.append(
                        f"今日はすでに{completion_summary['completed_count']}件完了しています。"
                    )
                if overdue:
                    parts.append(f"期限切れが{len(overdue)}件あります。")
                if duration_summary["timed_count"]:
                    parts.append(
                        "所要時間設定済みの予定は合計"
                        f"{_format_minutes(duration_summary['total_minutes'])}です。"
                    )
                if duration_summary["missing_count"]:
                    parts.append(
                        f"所要時間未設定が"
                        f"{duration_summary['missing_count']}件あります。"
                    )
                if next_item and next_item in items:
                    parts.append(
                        f"次は「{next_item['text']}」で、"
                        f"{format_reminder_due(next_item['due_at'])}です。"
                    )
                result = "".join(parts) + "\n" + _format_reminders(items)
        elif kind == "reminder_soon":
            from meina_reminders import reminders_within

            try:
                minutes = max(1, min(int(query or 30), 1440))
            except (TypeError, ValueError):
                minutes = 30
            items = reminders_within(minutes)
            if not items:
                result = f"{minutes}分以内の予定はありません。"
            else:
                result = (
                    f"{minutes}分以内の予定が{len(items)}件あります。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_next":
            from meina_reminders import (
                format_reminder_due,
                format_reminder_repeat,
                next_reminder,
            )

            item = next_reminder()
            if not item:
                result = "これからの予定はありません。"
            else:
                repeat = format_reminder_repeat(item)
                repeat_text = f"、{repeat}" if repeat else ""
                result = (
                    f"次の予定は「{item['text']}」です。"
                    f"{format_reminder_due(item['due_at'])}{repeat_text}です。"
                )
        elif kind == "reminder_today":
            from meina_reminders import today_reminders
            items = today_reminders()
            result = "今日の予定はありません。" if not items else "今日の予定です。\n" + _format_reminders(items)
        elif kind == "reminder_tomorrow":
            from meina_reminders import tomorrow_reminders
            items = tomorrow_reminders()
            result = "明日の予定はありません。" if not items else "明日の予定です。\n" + _format_reminders(items)
        elif kind == "reminder_week":
            from meina_reminders import week_reminders
            items = week_reminders()
            result = (
                "今週の予定はありません。"
                if not items
                else "今週の予定です。\n" + _format_reminders(items)
            )
        elif kind == "reminder_month":
            from meina_reminders import month_reminders
            items = month_reminders()
            result = (
                "今月の予定はありません。"
                if not items
                else "今月の予定です。\n" + _format_reminders(items)
            )
        elif kind == "reminder_overdue":
            from meina_reminders import overdue_reminders
            items = overdue_reminders()
            result = (
                "期限切れの予定はありません。"
                if not items
                else f"期限切れの予定が{len(items)}件あります。\n"
                + _format_reminders(items)
            )
        elif kind == "reminder_upcoming":
            from meina_reminders import upcoming_reminders
            items = upcoming_reminders()
            result = "今後の予定はありません。" if not items else "今後の予定です。\n" + _format_reminders(items)
        elif kind == "reminder_completed_period":
            from datetime import datetime, timedelta
            from meina_reminders import completion_events

            request = query if isinstance(query, dict) else {}
            current = datetime.now().astimezone()
            scope = str(request.get("scope") or "today")
            category = str(request.get("category") or "").strip() or None
            location = str(request.get("location") or "").strip() or None

            if scope == "month":
                start_date = current.date().replace(day=1)
                end_date = current.date()
                label = "今月"
            elif scope == "week":
                start_date = current.date() - timedelta(days=current.weekday())
                end_date = current.date()
                label = "今週"
            else:
                start_date = current.date()
                end_date = current.date()
                label = "今日"

            events = completion_events(
                start_date,
                end_date,
                current,
                category=category,
                location=location,
            )
            category_text = f"「{category}」カテゴリで" if category else ""
            location_text = f"場所が「{location}」で" if location else ""
            filter_text = category_text + location_text
            result = (
                f"{filter_text}{label}完了した予定の履歴はありません。"
                if not events
                else (
                    f"{filter_text}{label}完了した予定は{len(events)}件です。\n"
                    + _format_completion_events(events)
                )
            )
        elif kind == "reminder_completed_today":
            from datetime import datetime
            from meina_reminders import completion_events_for_date

            current = datetime.now().astimezone()
            events = completion_events_for_date(current.date(), current)
            result = (
                "今日完了した予定の履歴はありません。"
                if not events
                else f"今日完了した予定は{len(events)}件です。\n"
                + _format_completion_events(events)
            )
        elif kind == "reminder_completion_summary":
            from meina_reminders import completion_progress_summary

            requested_scope = str(query or "")
            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            else:
                scope, label = "today", "今日"
            summary = completion_progress_summary(scope=scope)
            completed_count = summary["completed_count"]
            remaining_count = summary["remaining_count"]
            result = (
                f"{label}は完了{completed_count}件、"
                f"残り{remaining_count}件です。"
            )
            if completed_count == 0 and remaining_count == 0:
                result = f"{label}は完了・未完了ともに記録対象の予定がありません。"
        elif kind == "reminder_location_progress":
            from datetime import datetime
            from meina_reminders import completion_location_progress

            current = datetime.now().astimezone()
            requested_scope = str(query or "")
            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            elif requested_scope == "tomorrow":
                scope, label = "tomorrow", "明日"
            else:
                scope, label = "today", "今日"
            progress = completion_location_progress(
                current.date(),
                current,
                scope=scope,
            )
            if not progress:
                result = f"{label}の場所別進捗に表示できる予定はありません。"
            else:
                parts = [
                    f"{location}は完了{counts['completed']}件、残り{counts['remaining']}件"
                    for location, counts in progress.items()
                ]
                result = f"{label}の場所別進捗は、" + "。".join(parts) + "です。"
        elif kind == "reminder_category_progress":
            from datetime import datetime
            from meina_reminders import completion_category_progress

            current = datetime.now().astimezone()
            requested_scope = str(query or "")
            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            elif requested_scope == "tomorrow":
                scope, label = "tomorrow", "明日"
            else:
                scope, label = "today", "今日"
            progress = completion_category_progress(
                current.date(),
                current,
                scope=scope,
            )
            if not progress:
                result = f"{label}のカテゴリ別進捗に表示できる予定はありません。"
            else:
                parts = [
                    f"{category}は完了{counts['completed']}件、残り{counts['remaining']}件"
                    for category, counts in progress.items()
                ]
                result = f"{label}のカテゴリ別進捗は、" + "。".join(parts) + "です。"
        elif kind == "reminder_category_summary":
            from meina_reminders import (
                reminder_category_counts,
                remaining_scope_reminders,
            )

            requested_scope = str(query or "")
            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            elif requested_scope == "tomorrow":
                scope, label = "tomorrow", "明日"
            else:
                scope, label = "today", "今日"
            items = remaining_scope_reminders(scope=scope)
            counts = reminder_category_counts(items)
            if not counts:
                result = f"{label}の未完了予定はありません。"
            else:
                parts = [
                    f"{category}が{count}件"
                    for category, count in counts.items()
                ]
                result = f"{label}のカテゴリ別件数は、" + "、".join(parts) + "です。"
        elif kind == "reminder_location_summary":
            from meina_reminders import (
                reminder_location_counts,
                remaining_scope_reminders,
            )

            requested_scope = str(query or "")
            if requested_scope == "month":
                scope, label = "month", "今月"
            elif requested_scope == "week":
                scope, label = "week", "今週"
            elif requested_scope == "tomorrow":
                scope, label = "tomorrow", "明日"
            else:
                scope, label = "today", "今日"
            items = remaining_scope_reminders(scope=scope)
            counts = reminder_location_counts(items)
            if not counts:
                result = f"{label}の未完了予定はありません。"
            else:
                parts = [
                    f"{location}が{count}件"
                    for location, count in counts.items()
                ]
                result = f"{label}の場所別件数は、" + "、".join(parts) + "です。"
        elif kind == "reminder_note_presence":
            from meina_reminders import (
                filter_reminders_by_note_presence,
                list_reminders,
                remaining_scope_reminders,
            )

            request = query if isinstance(query, dict) else {}
            requested_scope = str(request.get("scope") or "all")
            has_note = bool(request.get("has_note"))
            summary_only = bool(request.get("summary"))

            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            if requested_scope in scope_labels:
                items = remaining_scope_reminders(scope=requested_scope)
                label = scope_labels[requested_scope]
            else:
                items = list_reminders()
                label = ""

            filtered = filter_reminders_by_note_presence(
                items,
                has_note=has_note,
            )
            state_label = "メモ付き" if has_note else "メモ未設定"
            subject = (
                f"{label}の{state_label}予定"
                if label
                else f"{state_label}予定"
            )

            if summary_only:
                result = f"{subject}は{len(filtered)}件です。"
            elif not filtered:
                result = f"{subject}はありません。"
            else:
                result = (
                    f"{subject}は{len(filtered)}件です。\n"
                    + _format_reminders(filtered)
                )
        elif kind == "reminder_missing_location":
            from meina_reminders import reminders_missing_location

            items = reminders_missing_location()
            result = (
                "場所が未設定の予定はありません。"
                if not items
                else f"場所が未設定の予定は{len(items)}件です。\n"
                + _format_reminders(items)
            )
        elif kind == "reminder_location_list":
            from meina_reminders import (
                filter_reminders_by_metadata,
                remaining_scope_reminders,
                reminders_by_location,
            )

            request = query if isinstance(query, dict) else None
            if request is not None:
                location = str(request.get("location") or "").strip()
                requested_scope = str(request.get("scope") or "today")
                if requested_scope == "month":
                    scope, label = "month", "今月"
                elif requested_scope == "week":
                    scope, label = "week", "今週"
                elif requested_scope == "tomorrow":
                    scope, label = "tomorrow", "明日"
                else:
                    scope, label = "today", "今日"
                items = filter_reminders_by_metadata(
                    remaining_scope_reminders(scope=scope),
                    location=location,
                )
                result = (
                    f"{label}の場所が「{location}」の予定はありません。"
                    if not items
                    else f"{label}の場所が「{location}」の予定です。\n"
                    + _format_reminders(items)
                )
            else:
                location = str(query or "").strip()
                items = reminders_by_location(location)
                result = (
                    f"場所が「{location}」の予定はありません。"
                    if not items
                    else f"場所が「{location}」の予定です。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_category_list":
            from meina_reminders import (
                filter_reminders_by_metadata,
                remaining_scope_reminders,
                reminders_by_category,
            )

            request = query if isinstance(query, dict) else None
            if request is not None:
                category = str(request.get("category") or "").strip()
                requested_scope = str(request.get("scope") or "today")
                if requested_scope == "month":
                    scope, label = "month", "今月"
                elif requested_scope == "week":
                    scope, label = "week", "今週"
                elif requested_scope == "tomorrow":
                    scope, label = "tomorrow", "明日"
                else:
                    scope, label = "today", "今日"
                items = filter_reminders_by_metadata(
                    remaining_scope_reminders(scope=scope),
                    category=category,
                )
                result = (
                    f"{label}の「{category}」カテゴリの予定はありません。"
                    if not items
                    else f"{label}の「{category}」カテゴリの予定です。\n"
                    + _format_reminders(items)
                )
            else:
                category = str(query or "").strip()
                items = reminders_by_category(category)
                result = (
                    f"「{category}」カテゴリの予定はありません。"
                    if not items
                    else f"「{category}」カテゴリの予定です。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_setup_gap_summary":
            from meina_reminders import (
                reminder_setup_gap_counts,
                scope_reminders_including_paused,
            )

            request = query if isinstance(query, dict) else {}
            requested_scope = str(request.get("scope") or "all")
            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            source = scope_reminders_including_paused(
                scope=(
                    requested_scope
                    if requested_scope in scope_labels
                    else "all"
                ),
            )
            counts = reminder_setup_gap_counts(source)
            subject = (
                f"{scope_labels[requested_scope]}の設定不足内訳"
                if requested_scope in scope_labels
                else "設定不足内訳"
            )

            if not counts:
                result = f"{subject}はありません。すべて設定済みです。"
            else:
                parts = [
                    f"{label}{count}件"
                    for label, count in counts.items()
                ]
                result = f"{subject}は、" + "、".join(parts) + "です。"
        elif kind == "reminder_setup_complete":
            from meina_reminders import (
                reminders_fully_configured,
                scope_reminders_including_paused,
            )

            request = query if isinstance(query, dict) else {}
            requested_scope = str(request.get("scope") or "all")
            summary_only = bool(request.get("summary"))
            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            source = scope_reminders_including_paused(
                scope=(
                    requested_scope
                    if requested_scope in scope_labels
                    else "all"
                ),
            )
            items = reminders_fully_configured(source)
            subject = (
                f"{scope_labels[requested_scope]}の完全設定済み予定"
                if requested_scope in scope_labels
                else "完全設定済み予定"
            )

            if summary_only:
                result = f"{subject}は{len(items)}件です。"
            elif not items:
                result = f"{subject}はありません。"
            else:
                result = (
                    f"{subject}は{len(items)}件です。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_setup_gaps":
            from meina_reminders import (
                format_reminder_due,
                reminder_setup_gaps,
                scope_reminders_including_paused,
            )

            request = query if isinstance(query, dict) else {}
            requested_scope = str(request.get("scope") or "all")
            summary_only = bool(request.get("summary"))
            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            source = scope_reminders_including_paused(
                scope=(
                    requested_scope
                    if requested_scope in scope_labels
                    else "all"
                ),
            )
            gaps = reminder_setup_gaps(source)
            subject = (
                f"{scope_labels[requested_scope]}の設定不足予定"
                if requested_scope in scope_labels
                else "設定不足の予定"
            )

            if summary_only:
                result = f"{subject}は{len(gaps)}件です。"
            elif not gaps:
                result = f"{subject}はありません。"
            else:
                lines = []
                for entry in gaps:
                    item = entry["item"]
                    due_text = format_reminder_due(item.get("due_at", ""))
                    paused_text = "、一時停止中" if item.get("paused") else ""
                    missing_text = "・".join(entry["missing"])
                    lines.append(
                        f"・{item.get('text', '')}、{due_text}{paused_text}"
                        f"：{missing_text}"
                    )
                result = (
                    f"{subject}は{len(gaps)}件です。\n"
                    + "\n".join(lines)
                )
        elif kind == "reminder_important":
            from meina_reminders import (
                important_reminders,
                scope_reminders_including_paused,
            )

            request = query if isinstance(query, dict) else None
            if request is None:
                items = important_reminders()
                subject = "重要な予定"
                summary_only = False
            else:
                requested_scope = str(request.get("scope") or "all")
                summary_only = bool(request.get("summary"))
                scope_labels = {
                    "today": "今日",
                    "tomorrow": "明日",
                    "week": "今週",
                    "month": "今月",
                }
                if requested_scope in scope_labels:
                    source = scope_reminders_including_paused(
                        scope=requested_scope,
                    )
                    subject = f"{scope_labels[requested_scope]}の重要予定"
                else:
                    source = scope_reminders_including_paused(scope="all")
                    subject = "重要な予定"
                items = [
                    item for item in source
                    if item.get("important")
                ]

            if summary_only:
                result = f"{subject}は{len(items)}件です。"
            elif not items:
                result = f"{subject}はありません。"
            else:
                result = (
                    f"{subject}は{len(items)}件です。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_paused_list":
            from meina_reminders import scope_reminders_including_paused

            request = query if isinstance(query, dict) else {}
            requested_scope = str(request.get("scope") or "all")
            summary_only = bool(request.get("summary"))
            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            source = scope_reminders_including_paused(
                scope=(
                    requested_scope
                    if requested_scope in scope_labels
                    else "all"
                ),
            )
            items = [
                item for item in source
                if item.get("paused")
            ]
            subject = (
                f"{scope_labels[requested_scope]}の一時停止中予定"
                if requested_scope in scope_labels
                else "一時停止中の予定"
            )

            if summary_only:
                result = f"{subject}は{len(items)}件です。"
            elif not items:
                result = f"{subject}はありません。"
            else:
                result = (
                    f"{subject}は{len(items)}件です。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_pre_notify_presence":
            from meina_reminders import (
                filter_reminders_by_pre_notify_presence,
                scope_reminders_including_paused,
            )

            request = query if isinstance(query, dict) else {}
            requested_scope = str(request.get("scope") or "all")
            has_pre_notify = bool(request.get("has_pre_notify"))
            summary_only = bool(request.get("summary"))
            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            source = scope_reminders_including_paused(
                scope=(
                    requested_scope
                    if requested_scope in scope_labels
                    else "all"
                ),
            )
            items = filter_reminders_by_pre_notify_presence(
                source,
                has_pre_notify=has_pre_notify,
            )
            state_label = (
                "事前通知あり"
                if has_pre_notify
                else "事前通知未設定"
            )
            subject = (
                f"{scope_labels[requested_scope]}の{state_label}予定"
                if requested_scope in scope_labels
                else f"{state_label}予定"
            )

            if summary_only:
                result = f"{subject}は{len(items)}件です。"
            elif not items:
                result = f"{subject}はありません。"
            else:
                result = (
                    f"{subject}は{len(items)}件です。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_recurring_list":
            from meina_reminders import (
                filter_recurring_reminders,
                scope_reminders_including_paused,
            )

            request = query if isinstance(query, dict) else {}
            requested_scope = str(request.get("scope") or "all")
            summary_only = bool(request.get("summary"))
            scope_labels = {
                "today": "今日",
                "tomorrow": "明日",
                "week": "今週",
                "month": "今月",
            }
            source = scope_reminders_including_paused(
                scope=(
                    requested_scope
                    if requested_scope in scope_labels
                    else "all"
                ),
            )
            items = filter_recurring_reminders(source)
            subject = (
                f"{scope_labels[requested_scope]}の繰り返し予定"
                if requested_scope in scope_labels
                else "繰り返し予定"
            )

            if summary_only:
                result = f"{subject}は{len(items)}件です。"
            elif not items:
                result = f"{subject}はありません。"
            else:
                result = (
                    f"{subject}は{len(items)}件です。\n"
                    + _format_reminders(items)
                )
        elif kind == "reminder_deleted_list":
            from meina_reminders import (
                format_reminder_due,
                list_deleted_reminders,
            )
            items = list_deleted_reminders(limit=20)
            if not items:
                result = "最近削除した予定はありません。"
            else:
                lines = []
                for item in items:
                    deleted = format_reminder_due(item.get("deleted_at", ""))
                    due = format_reminder_due(item.get("due_at", ""))
                    lines.append(
                        f"・{item.get('text', '')}、予定:{due}、削除:{deleted}"
                    )
                result = (
                    f"最近削除した予定は{len(items)}件です。\n"
                    + "\n".join(lines)
                )
        elif kind == "reminder_list":
            from meina_reminders import list_reminders
            items = list_reminders()
            result = "未完了のリマインダーはありません。" if not items else "未完了のリマインダーです。\n" + _format_reminders(items)
        elif kind == "reminder_move_free":
            from datetime import datetime, timedelta
            from meina_reminders import (
                filter_reminders_by_due,
                find_first_free_slot,
                find_reminders,
                format_reminder_due,
                format_reminder_duration,
                move_reminder_occurrence,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")
            current = datetime.now().astimezone()
            day_offset = 1 if request.get("day") == "明日" else 0
            target_date = (current + timedelta(days=day_offset)).date()

            if not query_text:
                result = "空き時間へ移す予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の移動対象が見つかりませんでした。"
                        if has_due_filter
                        else "空き時間へ移す予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    try:
                        required = int(item.get("duration_minutes") or 0)
                        start_at = current.replace(
                            year=target_date.year,
                            month=target_date.month,
                            day=target_date.day,
                            hour=int(request.get("start_hour", 0)),
                            minute=int(request.get("start_minute", 0)),
                            second=0,
                            microsecond=0,
                        )
                        end_at = current.replace(
                            year=target_date.year,
                            month=target_date.month,
                            day=target_date.day,
                            hour=int(request.get("end_hour", 0)),
                            minute=int(request.get("end_minute", 0)),
                            second=0,
                            microsecond=0,
                        )
                    except (TypeError, ValueError):
                        result = "移動先の時間帯を読み取れませんでした。"
                    else:
                        if required <= 0:
                            result = (
                                f"「{item['text']}」には所要時間がありません。"
                                "先に所要時間を設定してください。"
                            )
                        else:
                            if day_offset == 0 and start_at < current:
                                start_at = current.replace(second=0, microsecond=0)
                                if start_at < current:
                                    start_at += timedelta(minutes=1)

                            slot = (
                                find_first_free_slot(
                                    start_at,
                                    end_at,
                                    required_minutes=required,
                                    exclude_reminder_id=item["id"],
                                )
                                if start_at < end_at
                                else None
                            )
                            if slot is None:
                                result = "指定した時間帯に移動できる空き時間がありません。"
                            else:
                                slot_start, _ = slot
                                moved = move_reminder_occurrence(
                                    item["id"],
                                    slot_start.isoformat(timespec="seconds"),
                                )
                                if moved:
                                    repeat_note = (
                                        "今回はこの時間に移し、次回の繰り返し時刻は元のままです。"
                                        if moved.get("repeat_rule")
                                        else ""
                                    )
                                    pause_note = (
                                        "通知は一時停止中のままです。"
                                        if moved.get("paused")
                                        else ""
                                    )
                                    result = (
                                        f"「{moved['text']}」を空いている時間へ移しました。"
                                        f"新しい時間は{format_reminder_due(moved['due_at'])}から"
                                        f"{format_reminder_duration(moved)}です。"
                                        f"{repeat_note}{pause_note}"
                                    )
                                else:
                                    result = f"「{query_text}」を空き時間へ移動できませんでした。"
        elif kind == "reminder_detail":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_category,
                format_reminder_due,
                format_reminder_duration,
                format_reminder_location,
                format_reminder_note,
                format_reminder_repeat,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "詳細を確認する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の詳細対象が見つかりませんでした。"
                        if has_due_filter
                        else "詳細を確認する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    due_text = format_reminder_due(item.get("due_at", ""))
                    duration_text = format_reminder_duration(item) or "未設定"
                    repeat_text = format_reminder_repeat(item) or "なし"
                    category_text = format_reminder_category(item) or "未分類"
                    location_text = format_reminder_location(item) or "未設定"
                    note_text = format_reminder_note(item) or "なし"
                    importance_text = "重要" if item.get("important") else "通常"
                    state_text = "一時停止中" if item.get("paused") else "通知中"
                    try:
                        notify_minutes = int(item.get("notify_before_minutes") or 0)
                    except (TypeError, ValueError):
                        notify_minutes = 0
                    notify_text = (
                        f"{notify_minutes}分前"
                        if notify_minutes > 0
                        else "なし"
                    )
                    result = (
                        f"「{item.get('text', '')}」の詳細です。"
                        f"日時:{due_text}、"
                        f"所要時間:{duration_text}、"
                        f"繰り返し:{repeat_text}、"
                        f"カテゴリ:{category_text}、"
                        f"重要度:{importance_text}、"
                        f"場所:{location_text}、"
                        f"事前通知:{notify_text}、"
                        f"状態:{state_text}、"
                        f"メモ:{note_text}。"
                    )
        elif kind == "reminder_duration":
            from meina_reminders import (
                filter_reminders_by_due,
                find_conflicting_reminders,
                find_reminders,
                format_reminder_due,
                format_reminder_duration,
                set_reminder_duration,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            duration_minutes = request.get("duration_minutes")
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "所要時間を変更する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の所要時間変更対象が見つかりませんでした。"
                        if has_due_filter
                        else "所要時間を変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    changed = set_reminder_duration(
                        matches[0]["id"],
                        duration_minutes,
                    )
                    if not changed:
                        result = f"「{query_text}」の所要時間を変更できませんでした。"
                    elif duration_minutes is None:
                        result = f"「{changed['text']}」の所要時間設定を解除しました。"
                    else:
                        result = (
                            f"「{changed['text']}」の所要時間を"
                            f"{format_reminder_duration(changed)}に変更しました。"
                        )
                        overlaps = find_conflicting_reminders(changed["id"])
                        if overlaps:
                            names = "、".join(
                                f"「{other.get('text', '')}」"
                                for other in overlaps[:3]
                            )
                            result += f" 変更後は{names}と時間が重なっています。"
        elif kind == "reminder_note":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                set_reminder_note,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            operation = str(request.get("operation") or "").strip().lower()
            note = request.get("note")
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "メモを確認・変更する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時のメモ対象が見つかりませんでした。"
                        if has_due_filter
                        else "メモを確認・変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    if operation == "get":
                        saved_note = str(item.get("note") or "").strip()
                        result = (
                            f"「{item['text']}」のメモは「{saved_note}」です。"
                            if saved_note
                            else f"「{item['text']}」にはメモがありません。"
                        )
                    elif operation == "set":
                        changed = set_reminder_note(item["id"], note)
                        result = (
                            f"「{changed['text']}」にメモを保存しました。"
                            if changed
                            else f"「{query_text}」のメモを保存できませんでした。"
                        )
                    elif operation == "clear":
                        changed = set_reminder_note(item["id"], None)
                        result = (
                            f"「{changed['text']}」のメモを削除しました。"
                            if changed
                            else f"「{query_text}」のメモを削除できませんでした。"
                        )
                    else:
                        result = "メモの操作内容を読み取れませんでした。"
        elif kind == "reminder_location":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                set_reminder_location,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            operation = str(request.get("operation") or "").strip().lower()
            location = request.get("location")
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "場所を確認・変更する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の場所対象が見つかりませんでした。"
                        if has_due_filter
                        else "場所を確認・変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    if operation == "get":
                        saved_location = str(item.get("location") or "").strip()
                        result = (
                            f"「{item['text']}」の場所は「{saved_location}」です。"
                            if saved_location
                            else f"「{item['text']}」には場所が設定されていません。"
                        )
                    elif operation == "set":
                        changed = set_reminder_location(item["id"], location)
                        result = (
                            f"「{changed['text']}」の場所を「{changed.get('location')}」に設定しました。"
                            if changed
                            else f"「{query_text}」の場所を設定できませんでした。"
                        )
                    elif operation == "clear":
                        changed = set_reminder_location(item["id"], None)
                        result = (
                            f"「{changed['text']}」の場所設定を解除しました。"
                            if changed
                            else f"「{query_text}」の場所設定を解除できませんでした。"
                        )
                    else:
                        result = "場所の操作内容を読み取れませんでした。"
        elif kind == "reminder_category":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                set_reminder_category,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            category = request.get("category")
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "カテゴリを変更する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時のカテゴリ変更対象が見つかりませんでした。"
                        if has_due_filter
                        else "カテゴリを変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    changed = set_reminder_category(
                        matches[0]["id"],
                        category,
                    )
                    if changed:
                        result = (
                            f"「{changed['text']}」を"
                            f"「{changed.get('category')}」カテゴリにしました。"
                            if category is not None
                            else f"「{changed['text']}」のカテゴリを解除しました。"
                        )
                    else:
                        result = f"「{query_text}」のカテゴリを変更できませんでした。"
        elif kind == "reminder_importance":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                set_reminder_importance,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            important_flag = bool(request.get("important"))
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "重要設定を変更する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の重要設定対象が見つかりませんでした。"
                        if has_due_filter
                        else "重要設定を変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    changed = set_reminder_importance(
                        matches[0]["id"],
                        important_flag,
                    )
                    if changed:
                        result = (
                            f"「{changed['text']}」を重要な予定にしました。"
                            if important_flag
                            else f"「{changed['text']}」の重要設定を解除しました。"
                        )
                    else:
                        result = f"「{query_text}」の重要設定を変更できませんでした。"
        elif kind in ("reminder_pre_notify_set", "reminder_pre_notify_clear"):
            from meina_reminders import (
                clear_reminder_pre_notify,
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                set_reminder_pre_notify,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")
            notify_before = request.get("notify_before_minutes")

            if not query_text:
                result = "事前通知を変更する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の事前通知対象が見つかりませんでした。"
                        if has_due_filter
                        else "事前通知を変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    if kind == "reminder_pre_notify_set":
                        changed = set_reminder_pre_notify(
                            item["id"],
                            notify_before,
                        )
                        result = (
                            f"「{changed['text']}」を{changed['notify_before_minutes']}分前にも"
                            "通知するようにしました。"
                            if changed
                            else f"「{query_text}」の事前通知を設定できませんでした。"
                        )
                    else:
                        changed = clear_reminder_pre_notify(item["id"])
                        result = (
                            f"「{changed['text']}」の事前通知を解除しました。"
                            if changed
                            else f"「{query_text}」の事前通知を解除できませんでした。"
                        )
        elif kind in ("reminder_pause", "reminder_resume"):
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                pause_reminder,
                resume_reminder,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = (
                    "一時停止する予定名を指定してください。"
                    if kind == "reminder_pause"
                    else "再開する予定名を指定してください。"
                )
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    action_text = "一時停止" if kind == "reminder_pause" else "再開"
                    result = (
                        f"指定した日時の{action_text}対象が見つかりませんでした。"
                        if has_due_filter
                        else f"{action_text}する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    if kind == "reminder_pause":
                        if item.get("paused"):
                            result = f"「{item['text']}」はすでに一時停止中です。"
                        else:
                            changed = pause_reminder(item["id"])
                            result = (
                                f"「{changed['text']}」の通知を一時停止しました。"
                                if changed
                                else f"「{query_text}」を一時停止できませんでした。"
                            )
                    else:
                        if not item.get("paused"):
                            result = f"「{item['text']}」は一時停止されていません。"
                        else:
                            changed = resume_reminder(item["id"])
                            result = (
                                f"「{changed['text']}」の通知を再開しました。"
                                f"次回は{format_reminder_due(changed['due_at'])}です。"
                                if changed
                                else f"「{query_text}」を再開できませんでした。"
                            )
        elif kind == "reminder_repeat_set":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                format_reminder_repeat,
                set_reminder_repeat,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            repeat_rule = str(request.get("repeat_rule") or "").strip()
            repeat_day = request.get("repeat_day")
            repeat_weekday = request.get("repeat_weekday")
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "繰り返しを変更する予定名を指定してください。"
            elif not repeat_rule:
                result = "新しい繰り返し設定を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の繰り返し変更対象が見つかりませんでした。"
                        if has_due_filter
                        else "繰り返しを変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    changed = set_reminder_repeat(
                        matches[0]["id"],
                        repeat_rule,
                        repeat_day=repeat_day,
                        repeat_weekday=repeat_weekday,
                    )
                    if changed:
                        repeat_text = format_reminder_repeat(changed)
                        result = (
                            f"「{changed['text']}」の繰り返しを{repeat_text}に変更しました。"
                            f"次回は{format_reminder_due(changed['due_at'])}です。"
                        )
                    else:
                        result = f"「{query_text}」の繰り返しを変更できませんでした。"
        elif kind == "reminder_repeat_clear":
            from meina_reminders import (
                clear_reminder_repeat,
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "繰り返しを解除する予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の繰り返し予定が見つかりませんでした。"
                        if has_due_filter
                        else "繰り返しを解除する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    if not item.get("repeat_rule"):
                        result = f"「{item['text']}」は繰り返し予定ではありません。"
                    else:
                        cleared = clear_reminder_repeat(item["id"])
                        result = (
                            f"「{cleared['text']}」の繰り返しを解除しました。"
                            if cleared
                            else f"「{query_text}」の繰り返しを解除できませんでした。"
                        )
        elif kind == "reminder_snooze":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                snooze_reminder,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            delay_minutes = request.get("delay_minutes")
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "後ろに回す予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時のスヌーズ対象が見つかりませんでした。"
                        if has_due_filter
                        else "後ろに回す予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = snooze_reminder(
                        matches[0]["id"],
                        delay_minutes,
                    )
                    if item:
                        repeat_note = (
                            "今回はこの時間に回し、次回の繰り返し時刻は元のままです。"
                            if item.get("repeat_rule")
                            else ""
                        )
                        result = (
                            f"「{item['text']}」を{delay_minutes}分後に回しました。"
                            f"新しい時間は{format_reminder_due(item['due_at'])}です。"
                            f"{repeat_note}"
                        )
                    else:
                        result = f"「{query_text}」を後ろに回せませんでした。"
        elif kind == "reminder_reschedule":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                reschedule_reminder,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            due_at = str(request.get("due_at") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "変更する予定名を指定してください。"
            elif not due_at:
                result = "変更後の日時を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の変更対象が見つかりませんでした。"
                        if has_due_filter
                        else "変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = reschedule_reminder(matches[0]["id"], due_at)
                    if item:
                        result = (
                            f"「{item['text']}」の日時を"
                            f"{format_reminder_due(item['due_at'])}に変更しました。"
                        )
                    else:
                        result = f"「{query_text}」の日時を変更できませんでした。"
        elif kind == "reminder_rename":
            from meina_reminders import (
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
                rename_reminder,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            new_name = str(request.get("new_name") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "名前を変更する予定名を指定してください。"
            elif not new_name:
                result = "新しい予定名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の名前変更対象が見つかりませんでした。"
                        if has_due_filter
                        else "名前を変更する予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する予定が{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = rename_reminder(matches[0]["id"], new_name)
                    if item:
                        result = f"予定名を「{item['text']}」に変更しました。"
                    else:
                        result = f"「{query_text}」の予定名を変更できませんでした。"
        elif kind == "reminder_restore_deleted":
            from meina_reminders import (
                filter_reminders_by_due,
                find_deleted_reminders,
                format_reminder_due,
                restore_deleted_reminder,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "復元する予定名を指定してください。"
            else:
                matches = find_deleted_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の削除済み予定が見つかりませんでした。"
                        if has_due_filter
                        else "削除済みの予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する削除済み予定が"
                        f"{len(matches)}件あります。候補は{candidate_times}です。"
                        "日時をもう少し具体的に指定してください。"
                    )
                else:
                    restored = restore_deleted_reminder(matches[0]["id"])
                    result = (
                        f"「{restored['text']}」をゴミ箱から復元しました。"
                        if restored
                        else f"「{query_text}」を復元できませんでした。"
                    )
        elif kind == "reminder_restore_completed":
            from meina_reminders import (
                filter_reminders_by_due,
                find_completed_reminders,
                format_reminder_due,
                restore_completed_reminder,
            )

            request = query if isinstance(query, dict) else {}
            query_text = str(request.get("target") or "").strip()
            date_filter = request.get("date")
            hour_filter = request.get("hour")
            minute_filter = request.get("minute")

            if not query_text:
                result = "未完了に戻す予定名を指定してください。"
            else:
                matches = find_completed_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    result = (
                        "指定した日時の完了済み単発予定が見つかりませんでした。"
                        if has_due_filter
                        else "完了済みの単発予定が見つかりませんでした。"
                    )
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致する完了済み予定が"
                        f"{len(matches)}件あります。候補は{candidate_times}です。"
                        "日時をもう少し具体的に指定してください。"
                    )
                else:
                    restored = restore_completed_reminder(matches[0]["id"])
                    result = (
                        f"「{restored['text']}」を未完了に戻しました。"
                        if restored
                        else (
                            f"「{query_text}」は戻せませんでした。"
                            "定期予定の完了履歴は安全のため巻き戻しません。"
                        )
                    )
        elif kind in ("reminder_done", "reminder_delete"):
            from meina_reminders import (
                complete_reminder,
                delete_reminder,
                filter_reminders_by_due,
                find_reminders,
                format_reminder_due,
            )

            if isinstance(query, dict):
                query_text = str(query.get("target") or "").strip()
                date_filter = query.get("date")
                hour_filter = query.get("hour")
                minute_filter = query.get("minute")
            else:
                query_text = re.sub(
                    r"(リマインダー|リマインド)(を)?(完了|削除)(して|してください|お願い(?:します)?)?",
                    "",
                    query or "",
                ).strip(" 、。！？?")
                date_filter = None
                hour_filter = None
                minute_filter = None

            if not query_text:
                result = "対象のリマインダー名を指定してください。"
            else:
                matches = find_reminders(query_text)
                has_due_filter = any(
                    value is not None
                    for value in (date_filter, hour_filter, minute_filter)
                )
                if has_due_filter:
                    matches = filter_reminders_by_due(
                        matches,
                        date=date_filter,
                        hour=hour_filter,
                        minute=minute_filter,
                    )

                if not matches:
                    if has_due_filter:
                        result = "指定した日時の対象リマインダーが見つかりませんでした。"
                    else:
                        result = "対象のリマインダーが見つかりませんでした。"
                elif len(matches) > 1:
                    candidate_times = "、".join(
                        format_reminder_due(item.get("due_at", ""))
                        for item in matches[:3]
                    )
                    result = (
                        f"「{query_text}」に一致するリマインダーが{len(matches)}件あります。"
                        f"候補は{candidate_times}です。日時をもう少し具体的に指定してください。"
                    )
                else:
                    item = matches[0]
                    ok = (
                        complete_reminder(item["id"])
                        if kind == "reminder_done"
                        else delete_reminder(item["id"])
                    )
                    action = "完了" if kind == "reminder_done" else "削除"
                    result = (
                        f"「{item['text']}」を{action}しました。"
                        if ok
                        else f"「{item['text']}」を{action}できませんでした。"
                    )
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

    from meina_reminder_worker import start_reminder_worker

    if start_reminder_worker(speak):
        print("⏰ リマインダー監視 : ON")
    else:
        print("⏰ リマインダー監視 : すでに起動中")

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

            from meina_reminder_worker import stop_reminder_worker
            stop_reminder_worker()

            speak(
                "またね！"
            )

            break

        except SystemExit:

            print("")
            print(
                "🛑 めいなを終了します"
            )

            from meina_reminder_worker import stop_reminder_worker
            stop_reminder_worker()

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
