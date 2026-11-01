param(
    [string]$DistributionPath = (Join-Path $PSScriptRoot '..\dist\FocusPomodoro'),
    [switch]$AutoStart
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path $DistributionPath).Path
if (-not (Test-Path (Join-Path $source 'FocusPomodoro.exe'))) {
    throw 'Build FocusPomodoro.exe before installation.'
}
$version = Get-Date -Format 'yyyyMMdd-HHmmss'
$destination = Join-Path $env:LOCALAPPDATA "Programs\FocusPomodoro\$version"
if (Test-Path $destination) { throw 'Installation folder already exists.' }
New-Item -ItemType Directory -Path $destination | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $destination -Recurse
$exe = Join-Path $destination 'FocusPomodoro.exe'
$backup = Join-Path $destination 'shortcut-backups'
New-Item -ItemType Directory -Path $backup | Out-Null
$shell = New-Object -ComObject WScript.Shell
function Set-FocusShortcut([string]$Path) {
    if (Test-Path $Path) {
        $backupName = [guid]::NewGuid().ToString() + '.lnk'
        Copy-Item -LiteralPath $Path -Destination (Join-Path $backup $backupName)
        Add-Content -LiteralPath (Join-Path $backup 'restore.txt') -Value "$backupName`t$Path" -Encoding UTF8
    }
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $exe
    $shortcut.Arguments = ''
    $shortcut.WorkingDirectory = $destination
    $shortcut.Description = 'Focus Pomodoro - desktop timer'
    $shortcut.IconLocation = "$exe,0"
    $shortcut.Save()
}
$desktop = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'Focus Pomodoro.lnk'
$programs = Join-Path ([Environment]::GetFolderPath('Programs')) 'Focus Pomodoro.lnk'
Set-FocusShortcut $desktop
Set-FocusShortcut $programs
if ($AutoStart) {
    $startupDir = [Environment]::GetFolderPath('Startup')
    $existing = @(Get-ChildItem -LiteralPath $startupDir -Filter '*.lnk' | Where-Object {
        $target = $shell.CreateShortcut($_.FullName).TargetPath
        [IO.Path]::GetFileName($target) -in @('PomodoroTimer.exe', 'FocusPomodoro.exe')
    })
    if ($existing.Count -gt 0) {
        foreach ($link in $existing) { Set-FocusShortcut $link.FullName }
    } else {
        Set-FocusShortcut (Join-Path $startupDir 'Focus Pomodoro.lnk')
    }
}
[PSCustomObject]@{Executable=$exe;Desktop=$desktop;Programs=$programs;AutoStart=[bool]$AutoStart;Backup=$backup} | ConvertTo-Json
