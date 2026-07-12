---
name: windows-computer-use-stable
description: Use when cua-driver fails with 0x0 capture, clicks don't land, keyboard input is unverified on Windows, or you need to automate browser tasks (GitHub token gen, form fill) without pixel-coordinate dependency. Provides MCP + mss/pyautogui stable layer + CDP/Selenium DOM control, coordinate conversion, Chrome fixed-position launch, and Snap Assist disable.
version: 2.2.0
platforms: [windows]
author: Hermes Agent + Community Solution
metadata:
  hermes:
    tags: [windows, computer-use, stable, mss, pyautogui, workaround, chrome]
    related_skills: [computer-use, windows-computer-use]
---

# Windows Computer Use — Stable Layer

## Overview

Standard `computer_use` on Windows fails due to known cua-driver bugs:

| Bug | Symptom | Root cause |
|-----|---------|------------|
| #52014 | `capture(mode="som")` returns 0×0 with 0 elements | Windows Graphics Capture compositor |
| #57905 | Window discovery returns empty list | cua-driver 0.7.x data.windows format |
| #59731 | Keyboard actions report success but `verified: false` | CUA driver keyboard backend |
| #59755 | Actions show success but don't land (click→docs navigation) | Binary ok/fail model |

This stable layer bypasses all four:

- **Capture:** MCP computer_use (works reliably)
- **Clicks:** `mss` pixel detection + `pyautogui` execution (bypasses #52014 / #57905)
- **Keyboard:** DOM-based via CDP or pyautogui (bypasses #59731)
- **Window position:** Fixed Chrome config (prevents coordinate drift)

## Package Contents

```
hermes-windows-computer-use/
├── chrome_stable.json              # Chrome — fixed position, no jumps
├── SKILL.md                        # This file
├── scripts/
│   ├── mss_click.py                # mss + pyautogui click engine
│   ├── coords.ps1                  # MCP ↔ global coordinate conversion
│   ├── disable-snap-assist.ps1     # Windows Snap Assist fix
│   ├── proc_watchdog.py            # Ghost process killer (Code.exe)
│   ├── vs_code_helper.py           # Safe VS Code launch with ghost detection
│   └── ps_monitor.py               # PowerShell process spawn monitor
├── templates/
│   └── silent_run.vbs              # Silent PowerShell — zero windows
├── tests/
│   ├── test_capture.ps1            # Capture dimension test
│   ├── test_click.ps1              # Button click test
│   ├── test_oauth.ps1              # OAuth flow test
│   └── test_failure.ps1            # Failure mode test
└── docs/
    ├── stable-architecture.md      # Architecture overview
    ├── coordinate-math.md           # Coordinate conversion math
    ├── oauth-flow.md               # OAuth consent flow steps
    ├── troubleshooting.md          # Common issues & fixes
    └── wallpaper-lockscreen.md     # Wallpaper + Lock Screen API guide

## What's New in v2.1.0

- **CDP Full Control** — Option C for keyboard/section 4: Selenium attached to Chrome debugging port for DOM-level browser automation. No pixel coordinates needed.
- **`references/github-token-cdp.md`** — Step-by-step guide for generating GitHub tokens via CDP (solves the common catch-22: need token → can't click generate token → need token).
```

## When to Use

- MCP `computer_use` capture returns 0×0 or empty element list
- MCP `left_click` reports success but lands on wrong element
- Keyboard actions show `verified: false` in response
- Chrome window jumps position after launch
- Any cua-driver failure on Windows

**Don't use when:** cua-driver works normally — prefer native computer_use for foreground accuracy.

## 1. Stable Chrome Configuration

**File:** `chrome_stable.json`

Prevents Chrome from jumping between positions (x=-8 fullscreen ↔ x=876 windowed):

```json
{
  "args": [
    "--window-position=0,0",
    "--window-size=1920,1080",
    "--disable-features=SnapAssist"
  ]
}
```

Key flags:
- `--window-position=0,0` — Chrome always starts at top-left
- `--window-size=1920,1080` — Fixed size = stable coordinates
- `--disable-features=SnapAssist` — No snap zone interference

## 2. Coordinate System

### MCP Screenshot Space
- Fixed: **1464 × 823** pixels
- All MCP `get_screenshot` results use this

### Global Desktop Space
- **1920 × 1080** (primary monitor)
- pyautogui operates in this space

### Conversion Formulas

**MCP → Global (click target):**
```
global_x = mcp_x × 1920 / 1464
global_y = mcp_y × 823 / 1080
```

**Global → MCP (screenshot lookup):**
```
mcp_x = global_x × 1464 / 1920
mcp_y = global_y × 823 / 1080
```

**File:** `scripts/coords.ps1` — PowerShell functions for both conversions.

## 3. Click Engine

### Primary: MCP `left_click`
Use MCP coordinates directly (fastest when it works).

### Fallback: `mss` + `pyautogui`
When MCP click fails to land:

```
python scripts/mss_click.py --x 1107 --y 506
python scripts/mss_click.py --color rozpocznij
```

**How it works:**
1. `mss` captures primary monitor in global coordinates
2. Scans for matching pixel color (button detection)
3. Converts to button center
4. `pyautogui.click()` at exact position

**⚠️ Caveat:** pyautogui moves the REAL OS cursor (steals foreground focus). Use only when MCP fails.

### Color Presets

| Preset | Button | RGB Range |
|--------|--------|-----------|
| `rozpocznij` | GCP "Rozpocznij" light blue | R:100–140, G:160–210, B:220–255 |
| `gcp_enable` | GCP "Włącz" blue | R:20–45, G:105–140, B:210–245 |
| `github_dark` | GitHub dark button | R:30–40, G:35–45, B:40–52 |

Tolerance: ±15 per channel.

## 4. Keyboard (bypass #59731)

When `computer_use(action="key", keys="tab")` shows `verified: false`:

### Option A — pyautogui (simplest)
```python
import pyautogui
pyautogui.press('tab')     # Single Tab
pyautogui.press('enter')   # Enter
pyautogui.write('text')    # Type text
```

### Option B — CDP (Chrome DevTools Protocol)
```javascript
// In browser console or CDP:
document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {
    key: 'Tab', code: 'Tab', keyCode: 9, which: 9, bubbles: true
}));
```

### Option C — CDP Full Control with Selenium (best for browser tasks)

For browser-heavy tasks (GitHub token generation, form filling, multi-step auth flows), attach Selenium to Chrome's remote debugging port. This bypasses ALL window-position, coordinate, and keyboard-layout problems because commands go directly to Chrome's DOM:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.debugger_address = "localhost:9222"
driver = webdriver.Chrome(options=options)

# Navigate and interact via DOM — no pixel coords needed
driver.get("https://github.com/settings/tokens")
driver.execute_script("document.querySelector('input').value = 'my-token'")
driver.execute_script("document.querySelector('button').click()")
```

**Key advantage:** No window focus, no pixel coordinates, no keyboard layout dependency. Works even when Chrome is minimized.

**See:** `references/github-token-cdp.md` for the full GitHub token generation workflow (solves the common blocker where computer_use can't generate a token due to window position issues).

## 5. Windows Snap Assist Fix

**Problem:** Windows Snap Assist resizes Chrome between snap zones, breaking coordinate alignment.

**Solution:** `scripts/disable-snap-assist.ps1`

```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts/disable-snap-assist.ps1
```

Sets registry values and restarts Explorer. Reboot recommended after first run.

## 6. Actions

### `stable_capture`
Capture Chrome window via MCP.

```
Result:
  - screenshot (image)
  - element list (from MCP)
  - dimensions: 1464×823
```

### `stable_click`
Click at a target using the best available method.

**Input:** button_label (color preset name) OR x,y (MCP coordinates)

**Process:**
1. Try MCP click with converted coordinates
2. If fail → use `mss_click.py` with color scan
3. Return status, method used, coordinates

### `stable_oauth_step`
Execute one step of OAuth consent flow.

**Input:** `step_name`: `rozpocznij`, `wlacz`, or custom

**Process:**
1. `stable_capture`
2. Find button by label or color preset
3. `stable_click`
4. Verify navigation (check for next form field)

## Workflow

### Complete OAuth Click Workflow

```
Step 1 — Launch Chrome with chrome_stable.json
Step 2 — stable_capture chrome
Step 3 — Find button in MCP element list
Step 4 — Convert coords using coords.ps1
Step 5 — stable_click
Step 6 — Verify navigation
```

### Test-Driven OAuth Sequence

```
1. Launch Chrome: url via clipboard → Ctrl+V → Enter
2. stable_capture → verify page loaded
3. stable_oauth_step(step_name="rozpocznij")
4. stable_capture → verify form loaded
5. Fill fields via pyautogui.write()
6. stable_oauth_step(step_name="wlacz")
7. stable_capture → verify consent screen
```

## Working Directory Policy

All temporary files (test scripts, debug output, generated content) go to:

```
K:\hermes_work\
├── scripts\     — reusable helpers
├── temp\        — one-shot/temporary files
└── output\      — execution results
```

**NEVER write files to the user's Desktop or Documents folder.** Use `K:\hermes_work\` for everything.

## Common Pitfalls

1. **pyautogui steals foreground.** User's cursor jumps. Warn before using. Prefer MCP `left_click` when possible.

2. **Color presets may need tuning.** Screen brightness, theme, or scaling shifts RGB values. Use `--discover` flag on `mss_click.py` to find actual colors:
   ```
   python scripts/mss_click.py --discover
   ```

3. **Chrome zoom ≠ coordinate scaling.** Only window size matters. Keep Chrome at 100% zoom or adjust conversion factor.

4. **Multiple monitors.** MCP targets the selected monitor. mss uses `monitors[2]` (primary). Adjust `MONITOR_INDEX` for secondary displays.

5. **Norton 360 blocks grab.exe.** Add cua-driver to antivirus exclusions manually. Without it, computer_use returns empty captures.

6. **Keyboard layouts.** URL entry via `type()` may produce wrong chars with non-EN layouts. Use clipboard paste (clip → Ctrl+V) for URLs, or use CDP Full Control (Option C) for browser tasks — it sends exact key codes regardless of OS keyboard layout.

7. **GitHub token generation catch-22.** You need a token → can't click "Generate token" because Chrome window position is wrong → can't get token. Solution: use CDP (Option C + `references/github-token-cdp.md`). Attach Selenium to `localhost:9222`, navigate to `github.com/settings/tokens`, and generate the token via DOM API — no pixel coordinates needed.

8. **PowerShell windows must NOT flash on user's desktop.** Calling `powershell.exe` directly from bash opens a visible window — extremely disruptive. Always use the VBS silent wrapper:

   ```bash
   cscript.exe //Nologo "path\to\silent_run.vbs" "path\to\script.ps1"
   ```

   **File:** `templates/silent_run.vbs` — keeps this pattern reusable across sessions.

9. **Desktop wallpaper ≠ Lock screen.** They are two completely separate Windows APIs:
   - **Wallpaper:** `SystemParametersInfo(0x0014, 0, path, 3)` via user32.dll — changes the desktop background
   - **Lock screen:** GPO policy at `HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization\\LockScreenImage` — changes the login screen
   
   See `docs/wallpaper-lockscreen.md` for both methods with full code examples.

10. **MCP server stuck on 1024×768 virtual monitor (fallback mode).** After killing all `node.exe` or `Code.exe` processes (e.g. `taskkill /F /IM node.exe`), the computer-use-mcp Electron overlay may lose display context. It reconnects to a software fallback monitor (1024×768) that has `"No screenshot source"`. Restarting the MCP server processes does NOT fix it — only a full system reboot restores real monitor detection.

    **Diagnosis:** `computer_toggle_session action=start` returns 1 monitor at 1024×768 with no visible apps. `get_screenshot` returns `"No screenshot source"`.

    **Workaround while waiting for reboot:** regular `computer_use` (cua-driver) still works for AX-tree based interaction (element indices with real bounds) and `list_apps`. Use `computer_use(action="click", element=N)` as fallback.

    **Prevention:** NEVER run `taskkill /F /IM node.exe` — it kills the MCP server. Kill only specific PIDs with `taskkill /PID N /F`.

11. **GUI apps (VS Code) spawn ghost processes from execute_code.** `subprocess.Popen(['code', folder])` with `CREATE_NO_WINDOW` or `DETACHED_PROCESS` creates Code.exe processes with no visible window. These block the real VS Code ("Another instance is already running"). `os.startfile(path)` may also fail ("server execution failed") from sandbox context.

    **Fix:** The user must open VS Code manually (taskbar icon or Start menu). Use `scripts/proc_watchdog.py` (in background) to auto-kill ghost Code.exe processes (no window → killed). Use `scripts/vs_code_helper.py` for safe launch attempts that check for ghosts first.

## Verification Checklist

- [ ] `chrome_stable.json` launches Chrome at fixed (0,0) 1920×1080
- [ ] MCP capture returns 1464×823 screenshot
- [ ] `mss_click.py --x 100 --y 100` clicks at correct global position
- [ ] Color scan finds the target button
- [ ] Coordinate conversion round-trips accurately (mss → MCP → global)
- [ ] Snap Assist is disabled (registry confirms)
- [ ] All 4 test scripts pass

## Test Suite

### test_capture.ps1
```powershell
$result = hermes stable_capture chrome
if ($result.screenshot.width -ne 1464) { throw "Bad width" }
if ($result.screenshot.height -ne 823) { throw "Bad height" }
Write-Host "Capture OK"
```

### test_click.ps1
```powershell
$result = hermes stable_click -button_label rozpocznij
if ($result.status -ne "success") { throw "Click failed" }
Write-Host "Click OK"
```

### test_oauth.ps1
```powershell
$result = hermes stable_oauth_step -step_name rozpocznij
if ($result.status -ne "success") { throw "OAuth step failed" }
Write-Host "OAuth OK"
```

### test_failure.ps1
```powershell
$result = hermes stable_click -button_label nonexistent
if ($result.status -ne "failed") { throw "Failure not detected" }
Write-Host "Failure mode OK"
```

## Provided Templates

| File | Purpose |
|------|---------|
| `templates/silent_run.vbs` | Silent PowerShell execution — runs `.ps1` scripts with **zero visible windows**. Required because `powershell.exe` from bash flashes disruptive windows on the user's desktop. |

```bash
# Usage from terminal (git-bash):
cscript.exe //Nologo "C:\path\to\silent_run.vbs" "C:\path\to\script.ps1"
```

## References

- Hermes issues: #52014, #57905, #59731, #59755
- cua-driver upstream: trycua/cua
- Hermes docs: https://hermes-agent.nousresearch.com/docs/
- Project: `D:\\Sorb\\projekty\\hermes-windows-computer-use\\`
- `references/github-token-cdp.md` — CDP-based GitHub token generation
- `references/wallpaper-lockscreen-api.md` — Wallpaper + Lock Screen API details, code examples, and silent execution methods
- `references/mcp-fallback-1024x768.md` — MCP server fallback monitor recovery
- `docs/wallpaper-lockscreen.md` — Same content as reference, in English for GitHub publication
