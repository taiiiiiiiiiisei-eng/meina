# Twitch自動切り抜きの初期設定

## 1. Twitch Developer Console

TwitchのDeveloper Consoleでアプリを作成し、Client IDとClient Secretを取得します。

## 2. ローカル設定

リポジトリ直下の `twitch_config.example.json` を `twitch_config.json` にコピーします。

`channel_login` に自分のTwitchログイン名を入れ、Client IDとClient Secretを入力してください。

`client_secret` はGitHubへアップロードしないでください。`twitch_config.json` は `.gitignore` に追加してローカルだけで使います。

## 3. 必要ソフト

- Python
- yt-dlp
- FFmpeg（PATHに追加）
- requests
- Ollama（面白い場面の判定を追加する段階で使用）
- faster-whisper（文字起こしを追加する段階で使用）

## 4. 動作確認

VOD取得だけを確認する場合:

```powershell
python twitch_clip_pipeline.py
```

自動監視:

```powershell
python twitch_auto_clip.py
```

自動監視は5分ごとに新しいアーカイブVODを確認します。

## 現在の段階

1. Twitch APIで最新VODを検出
2. 新しいVODだけを判定
3. yt-dlpでVODを取得
4. `twitch_vods/` に保存
5. 次の段階でWhisper + Ollama + FFmpegを接続して自動切り抜きを完成させる
