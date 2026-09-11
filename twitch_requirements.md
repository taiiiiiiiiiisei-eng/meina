# Twitch自動切り抜き機能

完成した流れ：

1. Twitch APIで最新VODを取得
2. yt-dlpでVODを保存
3. FFmpegで音声を16kHz WAVへ変換
4. faster-whisper `large-v3` で日本語文字起こし
5. Ollama `meina` が見どころを最大3件選択
6. FFmpegでMP4切り抜きを `clips/` に生成

## 必要な設定

`twitch_config.example.json` を `twitch_config.json` にコピーし、Twitch Developer Consoleで取得した `client_id` / `client_secret` と自分のチャンネルログイン名を設定してください。

`client_secret` はGitHubへ絶対にコミットしないでください。

## 手動テスト

```powershell
python twitch_auto_clip.py
```

または最新VODを直接指定：

```powershell
python twitch_ai_clipper.py twitch_vods/VIDEO_ID.mp4
```

## 音声命令

`meina_twitch.py` の `is_twitch_clip_request()` が、例えば「昨日の配信切り抜いて」「Twitchの配信を切り抜いて」「最近の配信のハイライト作って」を切り抜き命令として判定します。

既存の巨大な `meina_agent.py` を安全に全置換せず、Twitch機能を独立モジュールとして保守できる構成にしています。音声エージェント側から `run_twitch_clip_command()` を呼び出せば統合できます。
