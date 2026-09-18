$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = $null
if ($env:MEINA_PYTHON -and (Test-Path $env:MEINA_PYTHON)) {
  $python = $env:MEINA_PYTHON
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $python = (Get-Command python).Source
} else {
  Write-Host "❌ Pythonが見つかりません。"
  exit 1
}
$report = Join-Path $root "meina_error_report.txt"
$lines = New-Object System.Collections.Generic.List[string]
function Write-Report([string]$text) { $lines.Add($text); Write-Host $text }
Write-Report "============================================================"
Write-Report "🤖 めいな 開発チェック"
Write-Report "============================================================"
Write-Report ("日時: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Write-Report ("フォルダ: " + (Get-Location).Path)
Write-Report ""
Write-Report "【Git状態】"
$gitStatus = git status --short 2>&1
if ($LASTEXITCODE -eq 0) { if ($gitStatus) { $gitStatus | ForEach-Object { Write-Report ([string]$_) } } else { Write-Report "変更なし" } } else { Write-Report "Git状態を取得できませんでした。" }
Write-Report ""
Write-Report "【Python】"
$pythonVersion = & $python --version 2>&1
Write-Report ([string]$pythonVersion)
Write-Report ""
$files = @("meina_agent.py", "command_router.py", "meina2\tools.py", "meina_app.py")
Write-Report "【構文チェック】"
$syntaxOk = $true
foreach ($file in $files) {
  if (-not (Test-Path $file)) { Write-Report "❌ $file が見つかりません"; $syntaxOk = $false; continue }
  $out = & $python -m py_compile $file 2>&1
  if ($LASTEXITCODE -eq 0) { Write-Report "✅ $file" } else { $syntaxOk = $false; Write-Report "❌ $file"; $out | ForEach-Object { Write-Report ("    " + [string]$_) } }
}
Write-Report ""
Write-Report "【ルーター確認】"
$routerOk = $true
$routerTests = @("今日の天気を教えて", "明日の天気を教えて", "今の気温は？", "今日雨降る？")
foreach ($q in $routerTests) {
  $env:MEINA_TEST_TEXT = $q
  $code = 'import os, command_router; print(command_router.route_command(os.environ["MEINA_TEST_TEXT"], {"confidence": 1.0}))'
  $out = & $python -c $code 2>&1
  if ($LASTEXITCODE -eq 0) { Write-Report "✅ $q"; $out | ForEach-Object { Write-Report ("    " + [string]$_) } } else { $routerOk = $false; Write-Report "❌ $q"; $out | ForEach-Object { Write-Report ("    " + [string]$_) } }
}
Remove-Item Env:MEINA_TEST_TEXT -ErrorAction SilentlyContinue
Write-Report ""
Write-Report "【総合】"
if ($syntaxOk) { Write-Report "✅ 構文エラーなし" } else { Write-Report "❌ 構文エラーあり" }
if ($routerOk) { Write-Report "✅ ルーター確認OK" } else { Write-Report "❌ ルーター確認でエラー" }
Write-Report ("使用Python: " + $python)
Write-Report ""
Write-Report "このファイルをChatGPTに送れば、エラー解析に使えます。"
Write-Report "============================================================"
$lines | Set-Content -Path $report -Encoding UTF8
Write-Host ""
Write-Host "📄 レポート保存:"
Write-Host $report
if ($syntaxOk -and $routerOk) { exit 0 } else { exit 1 }