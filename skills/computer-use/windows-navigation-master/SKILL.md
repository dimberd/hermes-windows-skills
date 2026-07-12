---
name: windows-navigation-master
title: "Windows Navigation Master"
description: "Use when user needs to navigate Windows 11 — find files, open apps, switch browser tabs, manage bookmarks, open VS Code, search screen elements. Quick-reference workflows for the most common desktop operations."
version: 1.1.0
audience: user
tags: [windows, navigation, file-search, app-launch, browser, vscode]
category: computer-use
---

# Windows Navigation Master

## 1. Find Files Fast

```powershell
# By name (everywhere on C:)
Get-ChildItem -Path "C:\Users\PL_home" -Recurse -Filter "*partial_name*" -File -EA 0 |
  Select-Object FullName, Length | Format-Table -AutoSize

# By extension
Get-ChildItem -Path "C:\Users\PL_home" -Recurse -Filter "*.md" -File -EA 0

# Large files (>500 MB)
Get-ChildItem -Path "C:\" -Recurse -File -EA 0 |
  Where-Object { $_.Length -gt 500MB } |
  Select-Object @{N="MB";E={[math]::Round($_.Length/1MB)}}, FullName -First 20
```

From git-bash:
```bash
find /c/Users/PL_home -name "*partial*" -type f 2>/dev/null | head -20
```

## 2. Open Apps (VS Code, Chrome, Notepad)

### Method A: `code <path>` from git-bash (VS Code only — fastest)

When VS Code is in PATH (default install), the `code` CLI works directly from git-bash:

```python
# Open a folder/project in VS Code (returns instantly)
terminal(command='code /c/Users/PL_home/Desktop/hermes-windows-skills', timeout=10)

# Open a single file
terminal(command='code /c/Users/PL_home/Desktop/file.md', timeout=10)

# Open with --new-window to avoid mixing with existing tabs
terminal(command='code --new-window /c/Users/PL_home/Desktop/project', timeout=10)
```

After launching, use `focus_window` MCP tool or `ShowWindowAsync` (section 7) to bring it to front.

### Method B: PowerShell Start-Process (any app)

```python
# VS Code
terminal(command='powershell -Command "Start-Process -FilePath \'C:\\Users\\PL_home\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe\' -WindowStyle Maximized"', background=True, timeout=30)

# Chrome
terminal(command='powershell -Command "Start-Process -FilePath \'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\' -WindowStyle Maximized"', background=True, timeout=30)

# Notepad++
terminal(command='powershell -Command "Start-Process -FilePath \'C:\\Program Files\\Notepad++\\notepad++.exe\' -WindowStyle Maximized"', background=True, timeout=30)
```

## 3. Open VS Code with WSL project

```python
terminal(
    command='"/c/Users/PL_home/AppData/Local/Programs/Microsoft VS Code/Code.exe" --remote wsl+Ubuntu-26.04 /home/sorb_pl/hindsight',
    background=True, timeout=30
)
```

## 4. Browser: Navigate to URL (CDP method)

```python
import json, websocket
ws = websocket.create_connection("ws://localhost:9222/devtools/page/PAGE_ID", timeout=10)
ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://example.com"}}))
ws.close()
```

Find PAGE_ID:
```bash
curl -s http://localhost:9222/json | python -c "import json,sys; tabs=json.load(sys.stdin); [print(t['title'],t['id']) for t in tabs if ' нужный текст' in t['title']]"
```

## 5. Browser: Open bookmarks bar

Press `Ctrl+Shift+B` to toggle the bookmarks bar in Chrome/Edge.

## 6. Screen Navigation (computer_use)

```python
# Best: capture with SOM mode
computer_use(action="capture", mode="som", app="AppName")

# Click by element index (most reliable)
computer_use(action="click", element=14)

# Type text
computer_use(action="type", text="some text")

# Key combos
computer_use(action="key", keys="ctrl+s")
```

## 7. Win32 API for stubborn windows (minimized Electron apps)

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinAPI {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@
$proc = Get-Process "Code" -EA 0 | Select-Object -First 1
if ($proc) {
    [WinAPI]::ShowWindowAsync($proc.MainWindowHandle, 9)  # SW_RESTORE
}
```

## 8. Create/Write Files

```python
# write_file is best for creating files
write_file(path="C:\Users\PL_home\Desktop\test.txt", content="Hello World")

# From terminal:
echo "Hello" > /c/Users/PL_home/Desktop/test.txt
```

## 9. VS Code: Open File Cleanly

### Workflow (do this every time)

1. **ASK** user: "Залишити поточні вкладки чи відкрити нове вікно?"
2. **ALWAYS use `--new-window`** flag to avoid mixing with existing tabs
3. **Cyrillic filenames bug**: PowerShell does NOT pass UTF-8 Cyrillic paths correctly to VS Code (`Кибербезопасность.md` becomes `ĐSĐ,Đ±...`). **FIX: copy file to Desktop with ASCII name first:**
   ```bash
   cp "/h/GOOGLE_archiwum/books/markdown/Кибербезопасность.md" "/c/Users/PL_home/Desktop/cybersecurity.md"
   ```
   Then open the ASCII copy.
4. **Launch** via PowerShell Start-Process with `--new-window`:
   ```powershell
   Start-Process -FilePath "C:\Users\PL_home\AppData\Local\Programs\Microsoft VS Code\Code.exe" -ArgumentList '--new-window','C:\Users\PL_home\Desktop\cybersecurity.md' -WindowStyle Maximized
   ```
5. **Wait 5s**, then bring to front + maximize via Win32 API
6. **VERIFY** with screenshot that the file is visible and properly named

### Bring VS Code to Front after Launch

Windows may keep the previously active window (Chrome, Norton) on top. Run this after launch:

```powershell
Add-Type @'
using System; using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h, int n);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
}
'@
$p = Get-Process "Code" -EA 0 | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if ($p) {
    [W]::ShowWindowAsync($p.MainWindowHandle, 9) | Out-Null  # SW_RESTORE
    Start-Sleep -Milliseconds 200
    [W]::ShowWindowAsync($p.MainWindowHandle, 3) | Out-Null  # SW_MAXIMIZE
    [W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    [W]::BringWindowToTop($p.MainWindowHandle) | Out-Null
}
```

### Alternative: MCP `focus_window` tool (cleaner for non-Electron apps)

For non-Electron apps or when the PowerShell Win32 API is too heavy, use the MCP `focus_window` tool:

```python
# Start an MCP session first
mcp__computer_use_mcp__computer_toggle_session(action="start")
# → returns session_id + monitor info

# Bring an app to front by process name (case-insensitive, partial match OK)
mcp__computer_use_mcp__focus_window(name="Code")
# → returns {ok: true, focused: {hwnd: ..., pid: ..., title: "...", name: "Code"}}

# Then take a screenshot to verify
mcp__computer_use_mcp__computer_use(
    session_id=session_id,
    actions=[{"action": "get_screenshot", "monitor_id": monitor_id}]
)
```

**When to use which:**
- **MCP `focus_window`** — simple bring-to-front for non-Electron apps or after launch. One call.
- **PowerShell `ShowWindowAsync`** — Electron apps (VS Code, Discord, Teams) where background PostMessage doesn't work. Also needed when you need to restore from minimized AND maximize.
- **Both**: try `focus_window` first (faster), fall back to PowerShell if the window stays hidden.

### Check Window Layering

After launching, always check what's actually on screen:
```python
# Take screenshot and verify the target app is in front
mcp__computer_use_mcp__computer_use(session_id="...", actions=[{"action":"get_screenshot","monitor_id":"..."}])
# If another app is blocking (Chrome, Norton), minimize it first:
# Alt+Space → N (minimize active window)
```

## 10. PowerShell execution quirks (git-bash)

- Use `.ps1` files for complex PowerShell — inline `$_` breaks in git-bash
- Always use full Python path: `C:/Users/PL_home/AppData/Local/Programs/Python/Python310/python.exe`
- For read_file/write_file use Windows paths: `C:\\Users\\...`
- For terminal use MSYS paths: `/c/Users/...`
- For PowerShell with Cyrillic paths: save .ps1 as UTF-8 with BOM, OR copy file to ASCII name first

## 11. MCP Computer-Use Session Lifecycle

The MCP-based computer use tools (`mcp__computer_use_mcp__*`) operate through explicit sessions — they don't share state with the regular `computer_use()` tool function.

### Full workflow

```python
# 1. Start MCP session (acquires screenshot + input capability)
result = mcp__computer_use_mcp__computer_toggle_session(action="start")
session_id = result["session"]["session_id"]
monitors = result["session"]["monitors"]
# Pick the right monitor: primary has is_primary=True
primary = [m for m in monitors if m["is_primary"]][0]
monitor_id = primary["monitor_id"]

# 2. Focus an app window (by process name or PID)
mcp__computer_use_mcp__focus_window(name="Code")
# Can also focus by PID for exact targeting:
# focus_window(pid=28464)

# 3. Take screenshot of a specific monitor
result = mcp__computer_use_mcp__computer_use(
    session_id=session_id,
    actions=[{"action": "get_screenshot", "monitor_id": monitor_id}]
)
# Returns image path + structuredContent with visible_applications

# 4. Interact (keyboard, clicks, sleep between actions)
result = mcp__computer_use_mcp__computer_use(
    session_id=session_id,
    actions=[
        {"action": "key", "text": "ctrl+l"},
        {"action": "sleep", "duration_ms": 300},
        {"action": "type", "text": "https://example.com"},
        {"action": "key", "text": "Enter"},
        {"action": "sleep", "duration_ms": 3000},
        {"action": "get_screenshot", "monitor_id": monitor_id}
    ]
)

# 5. End session when done
mcp__computer_use_mcp__computer_toggle_session(action="end", session_id=session_id)
```

### Key differences vs regular computer_use()

| Aspect | Regular `computer_use()` | MCP `mcp__computer_use_mcp__*` |
|--------|--------------------------|-------------------------------|
| Session | Implicit, no session ID | Explicit session via toggle_session |
| Screenshot | SOM/AX overlay elements | Plain image + visible_apps metadata |
| Actions | Single action per call | Ordered action array (batched) |
| Monitor | Captures foreground window only | Selectable by monitor_id |
| Native dialogs | ❌ Background delivery blocked | ✅ OS-level mouse/keyboard input |
| Window focus | `focus_app()` background only | `focus_window()` can raise |

### When to use MCP session vs regular computer_use

- **MCP session** — native Windows dialogs (Save As), multi-monitor targeting, batched action sequences, when focus_window is needed
- **Regular computer_use** — simple SOM element clicks, AX set_value, single-step interactions, when no native dialog is involved
