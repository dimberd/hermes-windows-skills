---
name: windows-automation-enhanced
title: "Windows Automation Enhanced"
description: "Use when you need low-level Windows automation beyond computer_use — mouse/keyboard simulation via ctypes/pyautogui, file operations, window management, process control, and system interaction via Win32 API on Windows 10/11."
version: 1.0.0
audience: user
tags: [windows, automation, mouse, keyboard, file-ops, process]
category: system
---

# Windows Automation Enhanced

## When to Use
- Mouse/keyboard automation via Win32 API (ctypes) — clicks, drags, key combos
- Bulk file operations (copy, move, rename, delete) with batch patterns
- Window management — find, focus, move, resize, minimize/restore windows
- Process management — start, stop, list, monitor processes
- System interaction — volume control, display settings, clipboard access
- Complement to `computer_use` (cua-driver) when you need raw API access

## ⚠️ Critical: Keyboard Layout Check Before Typing

On Windows 10/11 with multiple keyboard layouts (Ukrainian/Polish/Russian/English), the active layout may produce wrong characters when typing URLs or commands. **ALWAYS check before any `computer_use` type action:**

```python
import ctypes
user32 = ctypes.windll.user32

def check_keyboard_layout():
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, None)
    locale_id = user32.GetKeyboardLayout(thread_id)
    lang_primary = (locale_id & 0xFFFF) & 0x3FF
    names = {0x09: "English", 0x22: "Ukrainian", 0x15: "Polish", 0x19: "Russian"}
    return names.get(lang_primary, f"0x{lang_primary:04X}")
```

If not English → use `Win+Space` to cycle layouts. Typical cycle: Укр → Рус → Eng → (loop).

## Core Python Snippets (Win32 via ctypes — no extra deps)

### Mouse Control
```python
import ctypes
from ctypes import wintypes

# Constants
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_WHEEL = 0x0800

user32 = ctypes.windll.user32

def click(x, y, button='left'):
    """Move mouse to (x,y) and click"""
    # Convert to absolute coordinates (0-65535)
    cx = int(x * 65535 / user32.GetSystemMetrics(0))
    cy = int(y * 65535 / user32.GetSystemMetrics(1))
    user32.SetCursorPos(x, y)
    if button == 'left':
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == 'right':
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

def get_cursor_pos():
    """Get current mouse position"""
    point = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def scroll_wheel(amount):
    """Scroll mouse wheel (positive=up, negative=down)"""
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, amount * 120, 0)
```

### Keyboard Control
```python
import ctypes

user32 = ctypes.windll.user32
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002

# Virtual key codes
VK = {
    'ENTER': 0x0D, 'TAB': 0x09, 'ESC': 0x1B,
    'BACK': 0x08, 'DELETE': 0x2E, 'SPACE': 0x20,
    'UP': 0x26, 'DOWN': 0x28, 'LEFT': 0x25, 'RIGHT': 0x27,
    'CTRL': 0x11, 'ALT': 0x12, 'SHIFT': 0x10,
    'WIN': 0x5B, 'F5': 0x74,
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'V': 0x56, 'X': 0x58, 'Z': 0x5A,
}

def press_key(vk_code):
    """Press and release a key by VK code"""
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYDOWN, 0)
    ctypes.windll.kernel32.Sleep(50)
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

def combo(keys):
    """Send a key combo, e.g. combo(['CTRL', 'C']) for Ctrl+C"""
    for k in keys:
        user32.keybd_event(VK[k], 0, KEYEVENTF_KEYDOWN, 0)
    ctypes.windll.kernel32.Sleep(50)
    for k in reversed(keys):
        user32.keybd_event(VK[k], 0, KEYEVENTF_KEYUP, 0)

def type_text(text):
    """Type text character by character (supports Unicode)"""
    for ch in text:
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x00C2, 0, ord(ch))
        # Alt: keybd_event approach for extended keys
```

### Window Management
```python
import ctypes

user32 = ctypes.windll.user32

def find_window(title_substring):
    """Find window handle by title substring (case-insensitive)"""
    result = []
    def enum_callback(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd) + 1
        title = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, title, length)
        if title_substring.lower() in title.value.lower():
            result.append((hwnd, title.value))
        return True
    EnumWindows = user32.EnumWindows
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    EnumWindows(EnumProc(enum_callback), 0)
    return result

def focus_window(hwnd):
    """Bring window to foreground"""
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)

def move_window(hwnd, x, y, width, height):
    """Move and resize window"""
    user32.MoveWindow(hwnd, x, y, width, height, True)

def minimize_window(hwnd):
    user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE

def maximize_window(hwnd):
    user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
```

### Process Management
```python
import subprocess, psutil  # pip install psutil

def list_processes(filter_name=None):
    """List running processes, optionally filtered by name"""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if filter_name and filter_name.lower() not in p.info['name'].lower():
            continue
        procs.append(p.info)
    return sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)

def kill_process(name_or_pid):
    """Kill process by name or PID"""
    if isinstance(name_or_pid, str):
        subprocess.run(['taskkill', '/F', '/IM', name_or_pid], check=False)
    else:
        subprocess.run(['taskkill', '/F', '/PID', str(name_or_pid)], check=False)

def start_process(path, args=None):
    """Start a process"""
    cmd = [path] + (args or [])
    return subprocess.Popen(cmd, shell=True)
```

### Bulk File Operations
```python
import shutil, os, glob, re
from pathlib import Path

def batch_rename(directory, pattern, replacement, dry_run=True):
    """Rename files matching regex pattern"""
    for f in os.listdir(directory):
        new_name = re.sub(pattern, replacement, f)
        if new_name != f:
            src = os.path.join(directory, f)
            dst = os.path.join(directory, new_name)
            print(f"{'[DRY]' if dry_run else ''} {f} -> {new_name}")
            if not dry_run:
                os.rename(src, dst)

def sync_dirs(src, dst, overwrite=False):
    """Sync files from src to dst"""
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            if overwrite or not os.path.exists(d):
                shutil.copy2(s, d)

def clean_temp_files():
    """Clean Windows temp directories"""
    for temp_dir in [os.environ.get('TEMP', ''), os.environ.get('TMP', '')]:
        if temp_dir and os.path.exists(temp_dir):
            for f in glob.glob(os.path.join(temp_dir, '*')):
                try:
                    if os.path.isfile(f): os.remove(f)
                except: pass
```

## Optional: Install pyautogui for Simpler API
```bash
pip install pyautogui pillow
```

Then:
```python
import pyautogui
pyautogui.click(x, y)
pyautogui.typewrite('hello', interval=0.05)
pyautogui.hotkey('ctrl', 'c')
pyautogui.screenshot('screenshot.png')
pyautogui.locateOnScreen('button.png')  # find by image
```

## ⚠️ CRITICAL: Keyboard Layout Check Before Typing

**Windows 10/11 with multiple keyboard layouts (УКР/PL/ENG):**
Before ANY keyboard input via computer_use/MCP, ALWAYS check and ensure English layout:

```python
import ctypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def ensure_english_keyboard():
    """Check current keyboard layout and switch to English if needed"""
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, None)
    locale_id = user32.GetKeyboardLayout(thread_id)
    lang_primary = (locale_id & 0xFFFF) & 0x3FF
    
    LANG_ENGLISH = 0x09  # 0x0409 English US
    LANG_UKRAINIAN = 0x22  # 0x0422
    LANG_POLISH = 0x15  # 0x0415
    
    lang_names = {0x09: "English", 0x22: "Ukrainian", 0x15: "Polish"}
    current = lang_names.get(lang_primary, f"0x{lang_primary:02X}")
    
    if lang_primary == LANG_ENGLISH:
        return True  # Already English
    
    # Switch: Win+Space cycles through layouts
    VK_LWIN, VK_SPACE = 0x5B, 0x20
    KEYEVENTF_KEYDOWN, KEYEVENTF_KEYUP = 0x0000, 0x0002
    
    for attempt in range(5):  # Max 5 presses to find English
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYDOWN, 0)
        user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYDOWN, 0)
        kernel32.Sleep(50)
        user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
        kernel32.Sleep(200)
        
        hwnd = user32.GetForegroundWindow()
        thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        locale_id = user32.GetKeyboardLayout(thread_id)
        lang_primary = (locale_id & 0xFFFF) & 0x3FF
        
        if lang_primary == LANG_ENGLISH:
            return True
    
    return False  # Failed to switch
```

**Typical layout cycle order:** Ukrainian (0x0422) → Russian (0x0419) → English (0x0409) → (loop)
So it may take 2-3 Win+Space presses.

### Chrome "Restore pages?" dialog handling
When Chrome crashes and shows "Restore pages?" dialog:
- Click **"Close"** button (bottom of dialog) — NOT the X button
- Or click **"Restore pages"** to restore previous tabs
- After closing, use `mcp__computer_use_mcp__focus_window(name='Google Chrome')` first to ensure Chrome is active
- Always verify with a screenshot after every action

### Multi-step GUI workflow pattern
1. ensure_english_keyboard() — check language first
2. focus_app / focus_window — ensure target app is active
3. Take screenshot to verify state
4. Perform click/type action
5. Take screenshot after action to verify result
6. Loop if result not as expected

## Chrome CDP — Faster Alternative to MCP computer_use

When `computer_use` / MCP is slow or unresponsive (common pattern: 0×0 captures, ClosedResourceError), use Chrome's built-in DevTools Protocol on port 9222:

```bash
# Chrome CDP is always running if Chrome was started with:
chrome.exe --remote-debugging-port=9222 --remote-allow-origins=*

# Check if available:
curl -s http://localhost:9222/json/version
```

**Python usage via websocket-client:**
```python
import requests, json, time, websocket

HTTP = "http://localhost:9222"
tabs = requests.get(f"{HTTP}/json").json()
tab = next(t for t in tabs if "google" in t["url"])
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)

def cdp(method, params=None):
    if params is None: params = {}
    mid = int(time.time() * 1000) % 100000
    ws.send(json.dumps({"id": mid, "method": method, "params": params}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == mid: return resp.get("result")

# Navigate, execute JS, extract data — all ~0.5s per action
cdp("Page.navigate", {"url": "https://example.com"})
result = cdp("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
```

**Speed comparison:**
| Method | Time per action | Notes |
|--------|----------------|-------|
| MCP computer_use | 3-6s | 250ms/action + npx launch |
| Win32 API (ctypes) | 0.1-0.3s | Key events, no artificial delay |
| Chrome CDP | 0.3-0.5s | WS protocol, no GUI needed |
| Background terminal | Async | Offload while other work runs |

## Pitfalls
- **Keyboard layout**: Check active layout before typing (Укр/Рус маппінг `/` `:` інакше). Використовуй `GetKeyboardLayout` через ctypes
- **Chrome "Restore pages?"**: Після перезапуску Chrome може показати діалог — закрий його перед діями
- **Python MS Store stub**: `python` — зламана заглушка (exit 49). Використовуй повний шлях
- **UAC prompts**: Some actions (elevated processes, system dirs) need admin rights
- **Focus**: `SendMessageW` for typing needs the target window to have focus
- **Python MS Store stub**: `python` may resolve to Store stub (exit 49, "nie znaleziono Python"). Use full path: `"C:/Users/PL_home/AppData/Local/Programs/Python/Python310/python.exe"`
- **psutil**: Install with `pip install psutil` for process monitoring
- **pyautogui**: Add `pyautogui.FAILSAFE = True` to enable emergency stop by moving mouse to corner
- **Screen coordinates**: On multi-monitor, the primary monitor is (0,0); secondary monitors have negative or positive offsets
- **File locks**: Running processes may lock files — use `handle.exe` (Sysinternals) to find lockers
- **UIPI — elevated windows invisible to cua-driver**: If the terminal runs as Administrator, any process spawned from it (VS Code via `code`, etc.) also runs as admin. `computer_use capture` returns 0×0 with 0 elements on those windows due to UIPI (User Interface Privilege Isolation). Detect with: `powershell -Command "[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"`. Fixes: (1) use `cmd /c start "" "path\to\app.exe"` to attempt non-elevated spawn; (2) ask user to open manually via desktop shortcut; (3) MCP `focus_window` sees elevated windows but `capture` still won't work — use raw Win32 API (ctypes from this skill) instead of `computer_use` for elevated targets.
