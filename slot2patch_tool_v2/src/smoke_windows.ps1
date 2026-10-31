# Windows 冻结包冒烟：帮助/空参数能启动，资源自检通过，GUI 能创建窗口。不使用 ROM。
param(
    [Parameter(Mandatory = $true)][string]$SrcDir,
    [Parameter(Mandatory = $true)][string]$ZipPath,
    [Parameter(Mandatory = $true)][string]$SummaryPath
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$log = New-Object System.Collections.Generic.List[string]
function Note([string]$msg) {
    Write-Host $msg
    $log.Add($msg)
}

function Save-Summary([int]$code) {
    $dir = Split-Path -Parent $SummaryPath
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
    Set-Content -LiteralPath $SummaryPath -Value ($log -join "`n") -Encoding utf8
    exit $code
}

Note "session:"
try { query session | ForEach-Object { Note $_ } } catch { Note "query session failed: $_" }

$distRoot = Join-Path $SrcDir "dist"
if (-not (Test-Path -LiteralPath $distRoot)) {
    Note "FAIL missing dist: $distRoot"
    Save-Summary 1
}
$appDir = Get-ChildItem -LiteralPath $distRoot -Directory | Select-Object -First 1
if (-not $appDir) {
    Note "FAIL no app directory under $distRoot"
    Save-Summary 1
}
$exe = Get-ChildItem -LiteralPath $appDir.FullName -Filter *.exe | Select-Object -First 1
if (-not $exe) {
    Note "FAIL no exe in $($appDir.FullName)"
    Save-Summary 1
}
Note "exe=$($exe.FullName)"

$tool = Get-ChildItem -LiteralPath $appDir.FullName -Recurse -Filter PatchToolForGbaR3.exe | Select-Object -First 1
$configs = Get-ChildItem -LiteralPath $appDir.FullName -Recurse -Directory -Filter configs |
    Where-Object { $_.FullName -match '\\_gba\\configs$' } | Select-Object -First 1
if (-not $tool) { Note "FAIL PatchToolForGbaR3.exe not in bundle"; Save-Summary 1 }
if (-not $configs) { Note "FAIL _gba/configs not in bundle"; Save-Summary 1 }
$jsonCount = (Get-ChildItem -LiteralPath $configs.FullName -Filter *.json -File).Count
Note "disk_tool=$($tool.FullName)"
Note "disk_configs=$($configs.FullName) json=$jsonCount"
if ($jsonCount -lt 1) { Note "FAIL no config json"; Save-Summary 1 }

$bad = Get-ChildItem -LiteralPath $appDir.FullName -Recurse -File |
    Where-Object { $_.Extension -match '^\.(gba|nds|sav)$' -or $_.Name -match '^(bios\.bin|gba_bios\.bin|nds_bios\.bin)$' }
if ($bad) {
    Note "FAIL ROM/BIOS-like files:"
    $bad | ForEach-Object { Note $_.FullName }
    Save-Summary 1
}

function Invoke-Frozen([string[]]$ArgList, [string]$Tag) {
    $out = Join-Path $env:TEMP "$Tag.out.txt"
    $err = Join-Path $env:TEMP "$Tag.err.txt"
    Remove-Item -LiteralPath $out, $err -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $exe.FullName -ArgumentList $ArgList -Wait -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $stdout = if (Test-Path -LiteralPath $out) { Get-Content -LiteralPath $out -Raw -Encoding utf8 } else { "" }
    $stderr = if (Test-Path -LiteralPath $err) { Get-Content -LiteralPath $err -Raw -Encoding utf8 } else { "" }
    Note "---- $Tag exit=$($p.ExitCode) args=$($ArgList -join ' ')"
    if ($stdout) { Note "stdout: $($stdout.Trim())" }
    if ($stderr) { Note "stderr: $($stderr.Trim())" }
    return @{ Code = $p.ExitCode; Out = "$stdout`n$stderr" }
}

$coreHelp = Invoke-Frozen @("--run-core", "--help") "core-help"
$lrHelp = Invoke-Frozen @("--run-lr", "--help") "lr-help"
$coreEmpty = Invoke-Frozen @("--run-core") "core-empty"
$lrEmpty = Invoke-Frozen @("--run-lr") "lr-empty"
$bundle = Invoke-Frozen @("--bundle-check") "bundle-check"

$ok = $true
if ($coreHelp.Code -ne 0 -or $coreHelp.Out -notmatch "--orig") { Note "FAIL --run-core --help"; $ok = $false }
if ($lrHelp.Code -ne 0 -or $lrHelp.Out -notmatch "--rom") { Note "FAIL --run-lr --help"; $ok = $false }
if ($coreEmpty.Code -eq 0) { Note "FAIL --run-core with no args should not succeed"; $ok = $false }
if ($lrEmpty.Code -eq 0) { Note "FAIL --run-lr with no args should not succeed"; $ok = $false }
if ($bundle.Code -ne 0 -or $bundle.Out -notmatch "tool_exists=True" -or $bundle.Out -notmatch "tk=") {
    Note "FAIL --bundle-check"
    $ok = $false
}

Add-Type @"
using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;
public static class WinEnum {
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  public static HashSet<uint> Want = new HashSet<uint>();
  public static List<string> Found = new List<string>();
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  public static bool Callback(IntPtr hWnd, IntPtr lParam) {
    uint pid;
    GetWindowThreadProcessId(hWnd, out pid);
    if (!Want.Contains(pid) || !IsWindowVisible(hWnd)) return true;
    var sb = new StringBuilder(512);
    GetWindowText(hWnd, sb, sb.Capacity);
    var title = sb.ToString();
    if (title.Length > 0) Found.Add(title);
    return true;
  }
}
"@

$gp = Start-Process -FilePath $exe.FullName -PassThru
Note "gui_pid=$($gp.Id)"
$found = $false
$titles = @()
$deadline = (Get-Date).AddSeconds(45)
$cb = [WinEnum+EnumProc]{ param($hWnd, $lParam) return [WinEnum]::Callback($hWnd, $lParam) }
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1
    if ($gp.HasExited) {
        Note "GUI exited early code=$($gp.ExitCode)"
        break
    }
    [WinEnum]::Want.Clear()
    [WinEnum]::Found.Clear()
    [void][WinEnum]::Want.Add([uint32]$gp.Id)
    Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $gp.Id } | ForEach-Object {
        [void][WinEnum]::Want.Add([uint32]$_.ProcessId)
    }
    [void][WinEnum]::EnumWindows($cb, [IntPtr]::Zero)
    $titles = @([WinEnum]::Found)
    if ($titles | Where-Object { $_ -match "slot2patch" }) { $found = $true; break }
}
Note "gui_windows=$($titles -join ' | ')"
if (-not $gp.HasExited) {
    & taskkill.exe /F /T /PID $gp.Id | Out-Host
    $gp.WaitForExit(10000) | Out-Null
}
if (-not $found) { Note "FAIL GUI window with title containing slot2patch was not created"; $ok = $false }
else { Note "GUI window created" }

if (-not $ok) { Save-Summary 1 }

Note "packing $ZipPath from $($appDir.FullName)"
& python (Join-Path $SrcDir "pack_windows_zip.py") $appDir.FullName $ZipPath
if ($LASTEXITCODE -ne 0) { Note "FAIL pack exit=$LASTEXITCODE"; Save-Summary 1 }
Save-Summary 0
