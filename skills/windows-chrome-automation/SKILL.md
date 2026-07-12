---
name: windows-chrome-automation
description: "Швидка автоматизація Chrome + Windows 11 через Win32 API (ctypes). Навігація, завантаження, кліки — без MCP (у 10x швидше)."
version: 1.0.0
author: SORB
tags: [windows, chrome, automation, win32, keyboard, google-drive]
---

# Windows Chrome Automation (Win32 API)

## Коли використовувати
- Навігація в Chrome за URL
- Завантаження файлів з Google Drive через браузер
- Кліки і введення тексту швидше ніж через MCP computer_use
- Коли MCP повільний або не працює

## Чому Win32 API швидше за MCP
MCP: 250ms затримка МІЖ кожним action + npx launch (~2-3s) + sleep(5000) = 10-15s на URL
Win32: без затримок, keybd_event миттєво = 2-3s на URL

## Базові константи Win32
```python
import ctypes, ctypes.wintypes, time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002

VK = {
    'LWIN': 0x5B, 'SPACE': 0x20, 'ENTER': 0x0D, 'TAB': 0x09,
    'ESC': 0x1B, 'BACK': 0x08, 'DELETE': 0x2E,
    'L': 0x4C, 'D': 0x44, 'A': 0x41, 'C': 0x43, 'V': 0x56, 'X': 0x58,
    'CTRL': 0x11, 'ALT': 0x12,
}

def key_down(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYDOWN, 0)

def key_up(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def press(vk):
    key_down(vk); kernel32.Sleep(30); key_up(vk)

def combo(*keys):
    for k in keys: key_down(VK[k])
    kernel32.Sleep(50)
    for k in reversed(keys): key_up(VK[k])

def type_text(text):
    """Type text character by character via WM_CHAR"""
    hwnd = user32.GetForegroundWindow()
    for ch in text:
        user32.PostMessageW(hwnd, 0x0102, ord(ch), 0)  # WM_CHAR
        kernel32.Sleep(10)
```

## Крок 1: Перевірка мови клавіатури
```python
def ensure_english_keyboard():
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, None)
    locale_id = user32.GetKeyboardLayout(thread_id)
    lang_primary = (locale_id & 0xFFFF) & 0x3FF
    if lang_primary == 0x09: return True  # вже English
    
    # Цикл УКР → RU → EN (до 5 спроб)
    for _ in range(5):
        key_down(VK['LWIN']); key_down(VK['SPACE'])
        kernel32.Sleep(50)
        key_up(VK['SPACE']); key_up(VK['LWIN'])
        kernel32.Sleep(200)
        
        hwnd = user32.GetForegroundWindow()
        thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        locale_id = user32.GetKeyboardLayout(thread_id)
        if ((locale_id & 0xFFFF) & 0x3FF) == 0x09: return True
    return False
```

## Крок 2: Навігація Chrome за URL
```python
def navigate_chrome(url):
    """Go to URL in active Chrome window"""
    # Focus address bar: Ctrl+L
    combo('CTRL', 'L')
    kernel32.Sleep(200)
    # Clear: Ctrl+A → Delete
    combo('CTRL', 'A')
    kernel32.Sleep(100)
    press(VK['DELETE'])
    kernel32.Sleep(100)
    # Type URL + Enter
    type_text(url)
    kernel32.Sleep(100)
    press(VK['ENTER'])
```

## Крок 3: Закриття діалогів Chrome
```python
def close_restore_pages_dialog():
    """Close 'Restore pages?' dialog by pressing Esc"""
    press(VK['ESC'])
    kernel32.Sleep(500)
    # If dialog still shows, try Tab+Enter to hit Close
    press(VK['TAB'])
    kernel32.Sleep(200)
    press(VK['ENTER'])
```

## 🚀 Chrome DevTools Protocol (CDP) — найшвидший спосіб

**Коли Win32 keyboard simulation теж повільний** — використовуй Chrome CDP через WebSocket.
Швидкість: миттєво, без затримок. Працює навіть коли Chrome згорнутий.

### Підключення
```python
import requests, json, time, websocket

HTTP_URL = "http://localhost:9222"
# Знайти вкладку
tabs = requests.get(f"{HTTP_URL}/json").json()
tab = next(t for t in tabs if "drive.google" in t["url"] or "КНИГИ" in t["title"])
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)

def cdp(method, params=None):
    if params is None: params = {}
    msg_id = int(time.time() * 1000) % 100000
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id: return resp.get("result")

# Навігація
cdp("Page.navigate", {"url": "https://example.com"})

# JavaScript
result = cdp("Runtime.evaluate", {
    "expression": "document.title",
    "returnByValue": True
})
print(result["result"]["value"])
```

### Google Drive — пошук і завантаження файлу
```python
# 1. Отримати file ID з DOM
result = cdp("Runtime.evaluate", {
    "expression": """
        (() => {
            const span = document.querySelector('span');
            // find by filename text
            let fileId = null;
            for (const el of document.querySelectorAll('[data-id]')) {
                if (el.textContent.includes('eTwierdzaLinux')) {
                    fileId = el.getAttribute('data-id');
                    break;
                }
            }
            return fileId;
        })()
    """,
    "returnByValue": True
})

# 2. Завантажити через прямий HTTP (швидше ніж через браузер)
file_id = result["result"]["value"]
dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/150"})
resp = session.get(dl_url, allow_redirects=True, timeout=30)

# Обробка confirm-токену (Google virus scan)
import re
if "confirm" in resp.text:
    confirm = re.search(r'confirm=([^"&]+)', resp.text).group(1)
    resp = session.get(
        f"https://drive.google.com/uc?export=download&confirm={confirm}&id={file_id}",
        allow_redirects=True, timeout=30
    )

with open("output.pdf", "wb") as f:
    f.write(resp.content)
```

## Повний workflow: завантажити PDF з Google Drive
```python
def download_drive_pdf(folder_url, filename=None):
    """Open shared Google Drive folder in browser"""
    ensure_english_keyboard()
    # Focus Chrome
    hwnds = find_windows("Chrome")
    if hwnds:
        user32.SetForegroundWindow(hwnds[0][0])
        kernel32.Sleep(500)
    # Close any dialogs
    close_restore_pages_dialog()
    # Navigate
    navigate_chrome(folder_url)
    time.sleep(5)  # wait for page load
```

## Пошук вікон
```python
def find_windows(title_substring):
    result = []
    def enum_cb(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        if title_substring.lower() in buf.value.lower():
            result.append((hwnd, buf.value))
        return True
    EnumWindows = user32.EnumWindows
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    EnumWindows(EnumProc(enum_cb), 0)
    return result
```

## Клік по координатах
```python
def click_at(x, y, button='left'):
    user32.SetCursorPos(x, y)
    kernel32.Sleep(50)
    if button == 'left':
        user32.mouse_event(0x0002, 0, 0, 0, 0)  # down
        kernel32.Sleep(50)
        user32.mouse_event(0x0004, 0, 0, 0, 0)  # up
    elif button == 'right':
        user32.mouse_event(0x0008, 0, 0, 0, 0)
        kernel32.Sleep(50)
        user32.mouse_event(0x0010, 0, 0, 0, 0)
```

## Pitfalls
1. **Мова клавіатури** — ЗАВЖДИ перевіряти перед набором!
2. **Chrome crash** — після crash буде "Restore pages?" діалог, закрити Esc
3. **Google Drive логін** — якщо не залогінений, буде сторінка логіну
4. **Focus** — Window must have focus for keyboard input to work
5. **Admin rights** — Деякі дії потребують прав адміна
6. **Для завантаження з Google Drive** — використовуй CDP + HTTP (reference: `google-drive-download.md`), не через GUI кліки

## Reference Files
- `references/google-drive-download.md` — Google Drive пошук + завантаження через Chrome CDP + прямий HTTP (confirm-токен, file ID з DOM)
