---
name: windows-app-launcher
title: "Windows App Launcher — System Level"
description: "Use when you need to launch, maximize, or manage Windows applications at system level — by direct executable path via PowerShell Start-Process, Win32 API, or CDP. Covers keyboard language switching, full-screen maximization, and app path registry on this system."
version: 1.0.0
audience: user
tags: [windows, launch, app, maximize, keyboard, system]
category: computer-use
---

# Windows App Launcher

## Registered App Paths (this system)

| App | Exe Path | Launch Command |
|-----|----------|----------------|
| Chrome | C:\Program Files\Google\Chrome\Application\chrome.exe | `Start-Process -FilePath "..."` |
| Edge | C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe | `Start-Process -FilePath "..."` |
| Brave | C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe | `Start-Process -FilePath "..."` |
| VS Code | C:\Users\PL_home\AppData\Local\Programs\Microsoft VS Code\Code.exe | `Start-Process -FilePath "..."` |
| Notepad++ | C:\Program Files\Notepad++\notepad++.exe | `Start-Process -FilePath "..."` |
| KeePassXC | C:\Program Files\KeePassXC\KeePassXC.exe | `Start-Process -FilePath "..."` |
| PowerShell | C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe | `Start-Process -FilePath "..."` |
| Task Manager | C:\Windows\System32\Taskmgr.exe | `Start-Process -FilePath "..."` |
| Explorer | C:\Windows\explorer.exe | `Start-Process -FilePath "..."` |
| Discord | %LOCALAPPDATA%\Discord\Update.exe | Update.exe --process-start Discord |

## Launch & Maximize (System Level — No Mouse)

```python
import subprocess, time

def launch_app(exe_path, args=None):
    """Launch app via PowerShell Start-Process (non-admin, no UAC, works in background)"""
    cmd = f'powershell -Command "Start-Process -FilePath \'{exe_path}\' -WindowStyle Maximized"'
    subprocess.Popen(cmd, shell=True)

def launch_and_maximize(exe_path, process_name):
    """Launch + maximize using Win32 API (for Electron apps)"""
    import subprocess
    subprocess.Popen(f'powershell -Command "Start-Process -FilePath \'{exe_path}\' -WindowStyle Maximized"', shell=True)
    time.sleep(5)
    # Restore + maximize via Win32
    ps_script = f'''
    Add-Type @"
    using System; using System.Runtime.InteropServices;
    public class W {{ [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h, int n); }}
"@
    $p = Get-Process "{process_name}" -EA 0 | Select-Object -First 1
    if($p) {{ [W]::ShowWindowAsync($p.MainWindowHandle, 9); Start-Sleep -Milliseconds 200; [W]::ShowWindowAsync($p.MainWindowHandle, 3) }}
    '''
    subprocess.run(['powershell', '-NoProfile', '-Command', ps_script], timeout=15)
```

## Keyboard Language Switching

Switch to English before typing URLs or commands in browser:

```python
# Method 1: Win+Space (cycles through layouts)
import subprocess
import ctypes

# Method 2: Win32 API — set English (US) layout
user32 = ctypes.windll.user32
# 0x04090409 = English (US) — keyboard layout identifier
user32.ActivateKeyboardLayout(0x04090409, 0)
```

## Quick Launch by App Name (One-liners)

```python
# Chrome
terminal('powershell -Command "Start-Process \'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\' -WindowStyle Maximized"', background=True, timeout=30)

# VS Code
terminal('powershell -Command "Start-Process \'C:\\Users\\PL_home\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe\' -WindowStyle Maximized"', background=True, timeout=30)

# Notepad++
terminal('powershell -Command "Start-Process \'C:\\Program Files\\Notepad++\\notepad++.exe\' -WindowStyle Maximized"', background=True, timeout=30)

# Brave
terminal('powershell -Command "Start-Process \'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe\' -WindowStyle Maximized"', background=True, timeout=30)
```

## Maximize Any Window (PowerShell Win32 API)

Use the reusable script at `scripts/restore_maximize.ps1` (takes process name as argument):

```bash
powershell -ExecutionPolicy Bypass -File "path/to/scripts/restore_maximize.ps1" Code
powershell -ExecutionPolicy Bypass -File "path/to/scripts/restore_maximize.ps1" chrome
```

Or inline:
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W { [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h, int n); }
"@
$p = Get-Process "ProcessName" -EA 0 | Select-Object -First 1
if ($p) {
    [W]::ShowWindowAsync($p.MainWindowHandle, 9)   # SW_RESTORE
    Start-Sleep -Milliseconds 200
    [W]::ShowWindowAsync($p.MainWindowHandle, 3)   # SW_MAXIMIZE
}
```

## Chrome CDP — Navigate to URL

```python
import json, websocket

# 1. Find Chrome tab
# curl -s http://localhost:9222/json

# 2. Navigate
ws = websocket.create_connection("ws://localhost:9222/devtools/page/PAGE_ID", timeout=10)
ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://example.com"}}))
ws.close()
```

## Special: VS Code + WSL Remote

```bash
"/c/Users/PL_home/AppData/Local/Programs/Microsoft VS Code/Code.exe" --remote wsl+Ubuntu-26.04 /home/sorb_pl/hindsight
```

## Pitfalls

- **DO NOT** use `Start-Process -Verb RunAs` — triggers UAC prompt
- **DO NOT** launch .exe directly in git-bash terminal — inherits admin rights, may crash renderer
- **For Electron apps** (VS Code, Discord, Chrome): use `ShowWindowAsync` for maximize — clicks on title bar buttons don't work in background
- **Language layout**: Check with `ctypes.windll.user32.GetKeyboardLayout(0)` before typing URLs
- **Cyrillic filenames in VS Code**: PowerShell corrupts UTF-8 Cyrillic paths when passing as arguments. FIX: copy file to Desktop with ASCII name first (`cp ".../Кибербезопасность.md" ".../Desktop/cybersecurity.md"`), then open the ASCII copy via `--new-window`.
- **Window layering**: After launching, always verify which app is in front via screenshot. If Chrome or Norton are blocking, minimize them via Win32 API ShowWindowAsync(hWnd, 6) (SW_MINIMIZE), then bring target to front with ShowWindowAsync(SW_RESTORE=9 → SW_MAXIMIZE=3) + SetForegroundWindow.
