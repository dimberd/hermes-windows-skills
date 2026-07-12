---
name: windows-computer-use
description: |-
  Windows-specific computer_use patterns: multi-monitor calibration,
  cua-driver config inspection, antivirus conflicts, accessibility
  tree quirks, and app launch troubleshooting on Windows 10/11.
version: 1.0.0
author: Hermes Agent Community
license: MIT
platforms: [windows]
keywords: [computer-use, windows, multi-monitor, desktop, gui, cua-driver]
---

# Windows Computer Use

This skill covers Windows-specific knowledge for `computer_use` tools that isn't
covered in generic cross-platform documentation. It applies to any Windows 10/11
system running Hermes Agent with the `computer_use` tool.

> **Note:** Paths in this skill use `$HOME` or `~` notation. On Windows, these
> resolve to `C:\Users\<YourUsername>` in bash/git-bash and to
> `$env:USERPROFILE` in PowerShell.

---

## Multi-monitor Setup

### Detecting Monitor Layout

Run this PowerShell to get monitor bounds, orientation, and primary status:

```powershell
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens |
    Select-Object DeviceName, Bounds, WorkingArea, Primary | Format-List
```

Key fields:
- **Bounds**: `{X, Y, Width, Height}` — position and size in virtual screen space
- **WorkingArea**: usable area excluding taskbar
- **Primary**: True/False — which is the primary display

### Coordinate System

Windows uses a unified virtual coordinate space across all monitors:

- Monitors can be positioned at any (X, Y) — they don't have to start at (0,0)
- Y can be negative (monitor positioned above the primary)
- The cua-driver's `capture(app="screen")` only returns the **primary monitor** image
- The SOM/AX tree CAN see elements on all monitors, but the screenshot is limited to the primary

### Understanding the Capture Limitation

Inspect cua-driver config:

```bash
cua-driver config
```

Typical output:
```json
{
  "capture_scope": "window",
  "max_image_dimension": 1568,
  "capture_mode": "ax"
}
```

- `capture_scope: "window"` — only the foreground window is captured, not the full desktop
- `max_image_dimension: 1568` — max pixel dimension for screenshots
- There is NO `cua-driver config set` command — config is read-only

### Working with Multiple Monitors

| Situation | Action |
|---|---|
| App is on secondary monitor | `capture(app="AppName")` to see that specific window |
| App process runs but no window | Process may be headless or renderer killed by security software |
| Need to bring app to primary | Tell user: `Win+Shift+←` (move window to primary monitor) |
| Need full desktop view | `capture(app="screen")` — but only primary monitor is captured |
| Click on secondary monitor | Use SOM element indices (span all monitors) or raw pixel coords |

### Click Coordinates Across Monitors

When clicking on the secondary monitor, the coordinate X value starts at the primary monitor's width:

- DISPLAY1 (1920×1080 at X=0): clicks at X ∈ [0, 1920)
- DISPLAY2 (1080×1920 at X=1920): clicks at X ∈ [1920, 3000)

Always prefer SOM element indices over raw coordinates when possible.

### Portrait vs Landscape

A secondary monitor in portrait mode reports `Width=1080, Height=1920` (swapped dimensions vs landscape). An app "full screen" on a portrait monitor matches that aspect ratio.

---

## Native Windows Save As Dialog Interaction

### Background: The Problem

When clicking a download link in Chrome, Windows opens a native "Save As" dialog (`Chrome_WidgetWin_1` class). The regular `computer_use` tool **cannot interact with this dialog in background mode** — clicks, key presses, and `set_value` on the address/combo fields all fail with:

```
Background delivery is not available for target window class
'Chrome_WidgetWin_1' on this event kind (mouse_click).
```

The dialog remains open and unresponsive to background automation.

### Solution: MCP computer_use tool

The MCP `computer_use` tool (from `computer_use_mcp`) can drive **native Windows dialogs** because it operates at the OS input level (mouse moves + clicks) rather than UIA PostMessage.

**Workflow:**

1. **End any existing cua-driver session** — the regular `computer_use` and MCP sessions conflict
2. **Start a fresh MCP session** to take a screenshot
3. **Take a screenshot** to find dialog position
4. **Click the Save/Zapisz button** via MCP mouse_move + left_click
5. **Fallback: use the dialog's accelerator key** — on localized Windows, `Alt+<first letter of save button>` triggers the action

### Coordinate System

MCP screenshots are returned at a different resolution than the monitor. Coordinates are **image-pixel proportional**:

```python
monitor_x = image_x / image_width * monitor_width
monitor_y = image_y / image_height * monitor_height
```

### The Keyboard Shortcut Approach (Most Reliable)

Once the user has navigated to the correct save folder:

```python
# Alt+Z = Save on Polish Windows (Zapisz)
mcp__computer_use_mcp__computer_use(
    session_id="...",
    actions=[{"action": "key", "text": "alt+z"}]
)
```

For English Windows, use `Alt+S` (Save). Find the accelerator by looking at the underlined letter in the button text.

### Limitations

- The MCP session has its own monitor enumeration — it may see a different layout than `computer_use`'s capture
- Only one MCP session is active at a time
- MCP captures show a cropped/rotated view on portrait secondary monitors
- The approach works best when the dialog is already positioned

---

## Web Downloads from Authenticated Services (Google Takeout, etc.)

### Golden Rule: NEVER Kill a Running Browser with Active Auth Sessions

Killing Chrome to restart it with `--remote-debugging-port` flags destroys the user's Google/authenticated session cookies. Even with `--user-data-dir` pointing to the same profile, Chrome's session state can be invalidated on restart.

### Preferred Workflows (In Order)

| # | Method | When to use |
|---|--------|-------------|
| 1 | **Ask user to click manually** | They are already on the page, can see it, and have the cursor |
| 2 | **SOM capture + element index click** | When `computer_use(action="capture", mode="som")` returns usable elements |
| 3 | **MCP computer_use with precise coordinates** | Only when SOM is broken AND you can see the screen |
| 4 | **CDP (Chrome DevTools Protocol) on an EXISTING instance** | Only if Chrome was already started with `--remote-debugging-port` |

### What NOT to Do

- ❌ **Do NOT kill `chrome.exe` and restart with `--remote-debugging-port`** — invalidates the user's Google session
- ❌ **Do NOT guess click coordinates blindly** — without vision feedback, you'll click at wrong positions
- ❌ **Do NOT use Tab+Enter keyboard navigation for multiple downloads** — unreliable for targeting specific buttons

### Browser URL Navigation Pitfall (Omnibox Redirect to Search)

When typing a URL into a browser address bar via MCP `type` action, modern Chromium browsers with combined address/search bars may interpret the input as a **search query** instead of a URL.

**Symptoms:** Typed `drive.google.com/...` and got Bing/YouTube search results. Repeated attempts still land on wrong page despite correct typing.

**Root cause:** Browser omnibox treats text without `https://` prefix as a search query. The `type` action sends characters at MCP inter-action speed (250ms) — the browser's input handler may lose `://` or leading characters.

**✅ Reliable workflow:**

```python
actions = [
    {"action": "key", "text": "ctrl+l"},
    {"action": "sleep", "duration_ms": 400},
    {"action": "key", "text": "ctrl+a"},
    {"action": "type", "text": "https://drive.google.com/drive/folders/XXXXX"},
    {"action": "key", "text": "Enter"},
    {"action": "sleep", "duration_ms": 5000},
    {"action": "get_screenshot", "monitor_id": "..."}
]
```

**Key rules:**
1. Always prepend `https://` — critical
2. `ctrl+a` after `ctrl+l` to clear old text
3. 400ms+ delay between address-bar key and type
4. 3-5s wait after Enter for slow auth
5. Capture to verify — never assume

### Clipboard Paste (Ctrl+V) — Most Reliable for URLs

When `set_value` is unavailable, use PowerShell to set clipboard content, then paste into the address bar. This bypasses keyboard layout entirely:

```bash
# Step 1: Copy URL to clipboard
powershell.exe -Command "Set-Clipboard -Value 'https://example.com'"

# Step 2: Paste + navigate via MCP key actions
# ctrl+l → ctrl+v → enter
```

MCP action sequence:
```python
actions = [
    {"action": "key", "text": "ctrl+l"},
    {"action": "sleep", "duration_ms": 200},
    {"action": "key", "text": "ctrl+v"},
    {"action": "sleep", "duration_ms": 300},
    {"action": "key", "text": "enter"},
    {"action": "sleep", "duration_ms": 3000}
]
```

### Keyboard Layout Check Before Browser Typing

When typing URLs or text into a browser via `type` action, the active Windows keyboard layout determines character output. If the active layout is not English-US, ASCII characters like `/`, `:`, `-` and URL letters produce wrong characters.

**Detection:** Use `GetKeyboardLayout` Win32 API via PowerShell to check the active layout ID before any browser `type` action.

**Preferred approaches (in order):**

1. **`set_value` on the address bar element** — bypasses keyboard layout entirely by setting the AX value directly on the address bar AXTextField.

2. **Ask the user to paste the URL** — fastest path when `set_value` doesn't work. They can use Win+Space to reach English themselves.

3. **CDP `Runtime.evaluate`** — only if Chrome was already started with `--remote-debugging-port`.

---

## Capture Returning 0×0 Despite All-Green Diagnostics

### Symptom

`computer_use` capture returns 0×0 / no elements, but `hermes computer-use doctor` says everything green:

```
✅ cua-driver 0.7.x on win32 — ok
✅ ax_capability: UIAutomation is reachable
✅ screen_capture_capability: D3D11 device reachable
```

All checks pass, but capture returns 0×0 width/height with zero elements in every mode.

### Remedies (In Order)

1. **Restart Hermes** (`/new` or restart the entire process) — most reliable fix
2. **End and restart MCP session** using `computer_toggle_session` (end then start)
3. **Restart Hermes + end/start MCP session** — combination of both
4. **Last resort:** Ask the user to perform the action manually

### Root Cause (Speculative)

The `computer_use` tool can enter a state where its internal compositor/screenshot source handle is stale — the doctor checks are at the OS/driver level (D3D11 reachable, UIA reachable), not at the compositor-pipeline level. A full process restart reinitializes the pipeline.

---

## App Window Detection Issues

### Symptom: `list_apps` Shows the Process but `capture(app="Name")` Returns Nothing

Common causes:

1. **Security software blocked the renderer** — Antivirus (Defender, Norton, etc.) may kill the child renderer process. Check with `cua-driver doctor` and look for access-denied errors.

2. **Running as Administrator** — Some apps (VS Code, Chrome) conflict when launched from an admin terminal. Use:
   ```bash
   runas /trustlevel:0x20000 "C:\path\to\app.exe"
   ```
   or PowerShell:
   ```powershell
   Start-Process -FilePath "C:\path\to\app.exe" -WindowStyle Maximized
   ```

3. **Headless process** — The process started without creating a UI window.

### cua-driver Config Inspection

```bash
cua-driver config
```

Returns JSON:
```json
{
  "capture_scope": "window",
  "max_image_dimension": 1568,
  "capture_mode": "ax",
  "version": "0.7.1"
}
```

Additional diagnostics:
```bash
cua-driver status
cua-driver doctor
cua-driver call get_screen_size
```

### Most Reliable App Launch (cua-driver launch_app)

When `computer_use` tools can't find an app, use cua-driver directly:

```bash
echo '{"path":"C:/path/to/app.exe"}' | cua-driver call launch_app
```

Returns PID + window info:
```json
{
  "pid": 20132,
  "running": true,
  "windows": [
    {"bounds": {...}, "title": "App Name", "window_id": 123456}
  ]
}
```

Then bring to front:
```bash
echo '{"pid":20132,"window_id":123456}' | cua-driver call bring_to_front
```

### Direct cua-driver Interaction Tools

**Bring window to front:**
```bash
echo '{"pid":20132,"window_id":1906388}' | cua-driver call bring_to_front
```
Note: `landed_on_target: false` means something else remained foreground.

**Click in window (pixel coords):**
```bash
echo '{"pid":20132,"window_id":1906388,"x":500,"y":300}' | cua-driver call click
```

If background delivery fails, try foreground:
```bash
echo '{"pid":20132,"window_id":1906388,"x":500,"y":300,"delivery_mode":"foreground"}' | cua-driver call click
```

**Get window state + UIA tree + screenshot:**
```bash
echo '{"pid":20132,"window_id":1906388}' | cua-driver call get_window_state
```

Returns:
- `elements[]` — structured UIA accessibility tree
- `tree_markdown` — human-readable tree
- `screenshot_png_b64` — base64-encoded window screenshot

**List all top-level windows:**
```bash
echo '{}' | cua-driver call list_windows
```

Returns `_legacy_windows[]` with pid, title, bounds, window_id for every visible window. Cross-monitor.

**Note:** The cua-driver binary is at:
```
%LOCALAPPDATA%\Programs\Cua\cua-driver\bin\cua-driver.exe
```

### Launch Methods Ranked by Reliability

| # | Method | Notes |
|---|--------|-------|
| 1 | `cua-driver call launch_app` via JSON pipe | ✅ Returns PID + window info directly |
| 2 | `powershell Start-Process -FilePath "..." -WindowStyle Maximized` | ✅ Good for most apps |
| 3 | Direct binary call in terminal | ❌ May inherit admin rights |

---

## Electron (Chrome_WidgetWin_1) Window Limitations

VS Code, Discord, Slack, Teams, and most modern desktop apps use Electron, which registers its window class as `Chrome_WidgetWin_1`. This causes specific limitations with background computer-use.

### Win+D (Show Desktop) Detection & Handling

**Win+D is a toggle:**
- First press → **Show Desktop** — minimizes all windows
- Second press → **Restore All** — restores all windows

**Detection:** After `capture(app="Name", mode="som")`:
- If **≤5 elements** visible (only Minimize/Maximize/Close buttons) → window is minimized
- If many elements (file tree, menus, etc.) → window is active

**🚫 `win+d` key combo is NOT supported by cua-driver:**
```python
computer_use(action="key", keys="win+d")  # Error: "Unknown key: d"
```

### ✅ Reliable Restore Method: PowerShell Win32 API

Alt+Tab/F11 via PostMessage **do NOT work** for background Electron windows. Use `ShowWindowAsync` via PowerShell:

```python
# Save this as a .ps1 file (avoid git-bash $_ issues)
restore_script = """
Add-Type @'
using System; using System.Runtime.InteropServices;
public class WinAPI {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
'@
$proc = Get-Process "$args" -EA 0 | Select-Object -First 1
if ($proc) {
    [WinAPI]::ShowWindowAsync($proc.MainWindowHandle, 9)  # SW_RESTORE
    Start-Sleep -Milliseconds 200
    [WinAPI]::ShowWindowAsync($proc.MainWindowHandle, 3)  # SW_MAXIMIZE
    [WinAPI]::SetForegroundWindow($proc.MainWindowHandle)
}
"""

terminal(command=f'powershell -ExecutionPolicy Bypass -Command "{restore_script}"', timeout=15)
```

### Title Bar Buttons (Minimize/Maximize/Close)

Background clicks (UIA Invoke via PostMessage) on Electron title bar buttons **report success but do not actually change window state**. This is because Electron renders custom chrome as `<webview>`-based elements that don't process background UIA events.

**🚫 What does NOT work for Electron:**
- ❌ Click on Maximize button → UIA Invoke returns OK, no visual change
- ❌ Alt+Tab via PostMessage → system hotkey not processed for background windows
- ❌ F11 via PostMessage → Electron doesn't receive background keyboard events
- ❌ Win+Up → processed by shell, not the window
- ❌ Win+D → "Unknown key: d"
- ❌ Alt+Space system menu → no response via PostMessage

**✅ What DOES work:**
- ✅ `focus_app` — targets the process (background, no visual change)
- ✅ PowerShell Win32 API (`ShowWindowAsync`) — actually restores/maximizes
- ✅ `list_apps` — shows available app names for targeting

### Full Maximize/Restore Procedure

```python
# 1. Launch
terminal(command='powershell Start-Process -FilePath "C:\\path\\to\\app.exe" -WindowStyle Maximized', background=True, timeout=30)
wait(5s)

# 2. Check state
capture(app="Name", mode="som")
if len(elements) <= 5:
    # 3. Restore via PowerShell Win32 API (only reliable method)
    terminal(command='powershell ... ShowWindowAsync ...', timeout=15)
    wait(2s)

# 4. Verify
capture(app="Name", mode="som")
```

### Other Electron Elements That May Fail in Background

- Custom title bar buttons (minimize/maximize/close in Electron chrome)
- Custom context menus rendered as DOM elements
- Drag-to-reorder in Electron-based file explorers
- Right-click DOM-based context menus

Always capture after an attempt to verify, and fall back to keyboard shortcuts or foreground interaction when state is unchanged.

---

## cua-driver Screen Size Check

```bash
cua-driver call get_screen_size
# Returns: {"width": 1920, "height": 1080} — primary monitor only
```

## cua-driver Health Check

```bash
cua-driver doctor
```

Watch for:
- `[warn] interactive session: session 1 desktop probe failed` — access denied to interactive desktop session
- `[ok] UI Automation: CoCreateInstance(CUIAutomation) succeeded` — UIA is working
- `EnumWindows visible: N windows` — total windows detected

---

## MCP Screenshot PID/App-Name Inconsistency

### Symptom

MCP `get_screenshot` and `get_context` return metadata with **wrong/stale PIDs and app names** that don't match what's actually visible in the screenshot image.

**Impact:** The `visible_applications` / `steps[i].monitor.visible_applications` arrays in the MCP response may be unreliable. The PID, title, and bounds may be stale — possibly from a window that was closed earlier.

### Root Cause (Likely)

MCP maintains an internal window enumeration cache that doesn't refresh between calls. When windows are closed and reopened (same process name, different PID), MCP still reports the old window info.

### Workarounds

| # | Method | Reliability |
|---|--------|:-----------:|
| 1 | **Read the actual screenshot image** via `vision_analyze` | ✅ Best |
| 2 | **Use CDP** (`curl http://localhost:9222/json`) for current tab titles and URLs | ✅ Also reliable |
| 3 | **Trust `get_context`** over `visible_applications` in screenshot response | ⚠️ Sometimes |
| 4 | **Ignore MCP `visible_applications` PID/title fields entirely** | ✅ Safe default |

### Verifying Screenshot Integrity

```bash
ls -la ~/AppData/Local/hermes/cache/images/img_*.png
```

Tiny files (under 20KB) mean the screenshot is mostly blank or corrupted. A proper screenshot at typical resolution should be 100KB-300KB.

### Summary

- MCP `visible_applications` metadata = unreliable for PID/title/bounds
- MCP screenshot image = accurate (verify file size > 20KB)
- `get_context` = more reliable than screenshot metadata
- CDP = most reliable for browser tab info

---

## .ps1 File Workaround for git-bash (PowerShell)

When running PowerShell from `terminal()` (git-bash/MSYS2), `$_` and `$()` are intercepted by MSYS2 path substitution.

### Problem

```powershell
# Broken — $_ becomes /c/Users/... (MSYS path expansion)
Get-Process | Where-Object { $_.MainWindowTitle -ne '' }

# Broken — $() triggers shell expansion before PowerShell
$p = Get-Process "Code" -EA 0 | Select-Object -First 1
```

### Symptoms

| You wrote | What git-bash sends to PowerShell | Result |
|-----------|----------------------------------|--------|
| `$_.Name` | `/c/Users/Username.Name` | ❌ CommandNotFoundException |
| `$_` | `/c/Users/Username` | ❌ Wrong value |
| `$($p.Id)` | `$(<expanded path>.Id)` | ❌ Parser error |

### Workarounds (In Preference Order)

#### 1. Save PowerShell script to .ps1 file (BEST)

```python
write_file(path="$HOME/script.ps1", content="""
Add-Type @'
using System; using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h, int n);
}
'@
$p = Get-Process "$args" -EA 0 | Select-Object -First 1
if ($p) {
    [W]::ShowWindowAsync($p.MainWindowHandle, 9) | Out-Null
}
""")
terminal('powershell -ExecutionPolicy Bypass -File "$HOME/script.ps1" Code', timeout=15)
```

#### 2. Escape `$_` with backtick (simple one-liners)

```powershell
powershell -NoProfile -Command "Get-Process | Where-Object { `$_.WorkingSet64 -gt 100MB }"
```

#### 3. Use `Get-CimInstance` to avoid pipeline variables

```powershell
# Instead of: Get-Process | Where-Object { $_.Name -eq "Code" }
# Use:
Get-CimInstance Win32_Process -Filter "Name='Code.exe'"
```

### When to Use Each

| Pattern | Preferred Workaround |
|---------|---------------------|
| Simple cmdlet with no pipeline | Inline `powershell -Command` OK |
| One-line filter with `$_` | Escape: `` `$_.Name `` |
| Multi-step script (5+ lines) | `.ps1` file via `-File` |
| Complex Win32 API calls | `.ps1` file (C# Add-Type blocks) |
| Any script with `$variables` | `.ps1` file |

---

## Additional Resources

### Keyboard Shortcut Cheatsheet for Dialog Navigation

| Windows Locale | Save Button | Accelerator |
|:--------------:|:-----------:|:-----------:|
| English | Save | `Alt+S` |
| Polish | Zapisz | `Alt+Z` |
| German | Speichern | `Alt+S` |
| French | Enregistrer | `Alt+E` |
| Spanish | Guardar | `Alt+G` |

### Common cua-driver JSON Commands

```bash
# Launch app
echo '{"path":"C:/path/to/app.exe"}' | cua-driver call launch_app

# Bring window to front
echo '{"pid":12345,"window_id":67890}' | cua-driver call bring_to_front

# Click in window (background)
echo '{"pid":12345,"window_id":67890,"x":500,"y":300}' | cua-driver call click

# Get window state + UIA tree
echo '{"pid":12345,"window_id":67890}' | cua-driver call get_window_state

# List all visible windows
echo '{}' | cua-driver call list_windows

# Get screen size
cua-driver call get_screen_size

# Check health
cua-driver doctor

# View config
cua-driver config
```

### cua-driver Binary Path

```
%LOCALAPPDATA%\Programs\Cua\cua-driver\bin\cua-driver.exe
```
