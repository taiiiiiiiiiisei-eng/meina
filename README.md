# めいな

ローカルで動作する JARVIS 型 AI アシスタント。

## AI開発ルール

このリポジトリはGPT/Codexによる継続的な開発を前提にしています。

- `AGENTS.md` — AI開発エージェント向けの設計・変更・テスト・Gitルール
- `ci_self_test.py` — 外部依存なしで実行できる静的セルフテスト
- `.github/workflows/static-self-test.yml` — push / pull request時の自動静的テスト

エージェントは、既存コードを確認 → 必要な変更だけ実装 → テスト → 結果を確認、の順で進めます。

## 構成

- `meina_agent.py` — 音声入力・Whisper・TTS・AI判断・PC操作の統合本体
- `run_meina.py` — 実行中のPython環境からCUDA DLLを自動検出して起動
- `meina_brain/brain_core.py` — 自作AIブレイン
- `meina2/tools.py` — PC操作・Web操作
- `command_router.py` — 安全なコマンド振り分け
- `self_test.py` — Whisper/Ollamaを起動せず構成を確認するセルフテスト
- `twitch_clip_pipeline.py` — Twitch VOD取得・音声抽出・Whisper文字起こし・FFmpeg切り抜き
- `twitch_ai_clipper.py` — Whisper候補をOllamaで評価して自動切り抜き
- `twitch_video_editor.py` — 字幕・映像効果・動画編集
- `meina_twitch.py` / `meina_twitch_voice.py` — めいなからTwitch切り抜きを呼び出す処理
- `twitch_auto_clip.py` — 新しいVODを定期監視して自動切り抜き

## 必要環境

- Windows 10 / 11
- Python 3.14+
- NVIDIA GPU + CUDA対応環境
- Ollama
- 日本語Windows音声（TTS用）
- FFmpeg / ffprobe
- Twitch Developer Application

## セットアップ

```powershell
git clone https://github.com/taiiiiiiiiiisei-eng/meina.git
cd meina
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python self_test.py
python ci_self_test.py
```

Ollamaでモデル `meina` を用意してから起動：

```powershell
python run_meina.py
```

または `start_meina.bat` を実行。安定版ランチャーとして現在の仮想環境から本体を起動します。

GUIアプリとして使う場合は `start_meina_app.bat` を実行してください。

## 音声操作

「メイナ」と呼びかけると待機し、その後の音声をWhisperで認識して処理します。

現在対応している主な操作：

- メモ帳 / 電卓 / エクスプローラーを開く
- Discord / Steam / Chrome / Edge / OBS / VALORANTなどのアプリ起動
- Google検索
- YouTube検索
- Webサイトを開く
- 日本語音声で返答
- 今日/明日の天気・気温・降水確率
- 現在時刻・日付・曜日
- PC状態（GPU・メモリ・ディスク）の確認
- リマインダー・予定の追加・確認・完了・削除
- Twitch配信のAI切り抜き処理

## Twitch AI切り抜き

めいなに「配信の切り抜きを作って」などと話しかけると、Twitchの最新アーカイブVODを対象に、次の流れで処理します。

1. Twitch APIで対象チャンネルの最新VODを取得
2. `yt-dlp` でVODを取得
3. FFmpegで音声を抽出
4. `faster-whisper` で日本語字幕・タイムスタンプを作成
5. 候補場面を抽出
6. Ollamaの `meina` が面白さ・驚き・上手さなどを評価
7. FFmpegでMP4切り抜きを作成
8. `clips/` に保存し、選定理由をJSONへ保存

Twitchの設定は `twitch_config.example.json` を `twitch_config.json` にコピーして、自分のチャンネルログイン名・Developer ApplicationのClient ID・Client Secretを設定してください。

```powershell
copy twitch_config.example.json twitch_config.json
python twitch_clip_runner.py "昨日の配信切り抜いて"
```

新しいVODを自動監視する場合：

```powershell
python twitch_auto_clip.py
```

### 注意

- `twitch_config.json` にはClient Secretが入るため、GitHubへコミットしないでください。
- VODの取得・利用はTwitchの利用規約や対象コンテンツの権利・アクセス条件に従ってください。
- 長時間VODのWhisper解析と動画エンコードには時間とストレージを使います。

## 注意

`.venv`、`__pycache__`、学習済みキャッシュ、Twitchの認証情報、VOD、切り抜き動画などの実行データはGitHubに含めず、各PCで構築してください。
