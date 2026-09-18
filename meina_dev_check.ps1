$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = $env:MEINA_PYTHON
if (-not $python -or -not (Test-Path $python)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}
if (-not $python -or -not (Test-Path $python)) {
    Write-Host "ERROR: Python was not found."
    exit 1
}

$report = Join-Path $root "meina_error_report.txt"
$lines = New-Object System.Collections.Generic.List[string]
function Add-Report([string]$text) {
    $lines.Add($text)
    Write-Host $text
}

Add-Report "MEINA DEVELOPMENT CHECK"
Add-Report "======================="
Add-Report ("Time: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Add-Report ("Folder: " + (Get-Location).Path)
Add-Report ("Python: " + $python)
Add-Report ""

$syntaxOk = $true
$files = @("meina_agent.py", "command_router.py", "meina2\tools.py", "meina_app.py")
Add-Report "[PYTHON SYNTAX]"
foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        Add-Report ("MISSING: " + $file)
        $syntaxOk = $false
        continue
    }
    $out = & $python -m py_compile $file 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-Report ("OK: " + $file)
    } else {
        $syntaxOk = $false
        Add-Report ("FAIL: " + $file)
        foreach ($item in $out) { Add-Report ("  " + [string]$item) }
    }
}

Add-Report "[ROUTER]"
$routerOk = $true
$tests = @(
    "import command_router; print(command_router.route_command("今日の天気を教えて", {"confidence": 1.0}))",
    "import command_router; print(command_router.route_command("明日の天気を教えて", {"confidence": 1.0}))",
    "import command_router; print(command_router.route_command("今の気温は？", {"confidence": 1.0}))",
    "import command_router; print(command_router.route_command("今日雨降る？", {"confidence": 1.0}))"
)
foreach ($code in $tests) {
    $out = & $python -c $code 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-Report "ROUTER OK"
        foreach ($item in $out) { Add-Report ("  " + [string]$item) }
    } else {
        $routerOk = $false
        Add-Report "ROUTER FAIL"
        foreach ($item in $out) { Add-Report ("  " + [string]$item) }
    }
}

Add-Report "[RESULT]"
if ($syntaxOk) { Add-Report "Syntax PASS" } else { Add-Report "Syntax FAIL" }
if ($routerOk) { Add-Report "Router PASS" } else { Add-Report "Router FAIL" }
$lines | Set-Content -Path $report -Encoding UTF8
Add-Report ("Report: " + $report)

if ($syntaxOk -and $routerOk) { exit 0 }
exit 1