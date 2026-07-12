# Troubleshooting Guide

## Common Issues

### 1. Capture Returns 0×0 or Empty

**Symptoms:**
- `computer_use(action="capture")` returns `{width: 0, height: 0}`
- Zero elements returned in any mode (som, vision, ax)
- `hermes computer-use doctor` reports all green

**Remedies (in order):**
1. Restart Hermes (`/new` or restart process) — most reliable
2. End and restart MCP session using `computer_toggle_session`
3. Combination of both restarts
4. Ask user to perform the action manually

### 2. App Not Found by capture()

**Symptoms:**
- `list_apps` shows the process
- `capture(app="Name")` returns "no on-screen window"

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Antivirus blocking renderer | Check cua-driver doctor for access-denied |
| Running as Administrator | Use `Start-Process -WindowStyle Maximized` |
| Headless process | Process has no UI window |

### 3. Electron Window Won't Restore

**Symptoms:**
- Clicking Maximize button reports OK but nothing changes
- Alt+Tab/F11 don't work

**Fix:** Use PowerShell Win32 API:

```powershell
Add-Type @'
using System; using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h, int n);
}
'@
$p = Get-Process "Code" -EA 0 | Select-Object -First 1
[W]::ShowWindowAsync($p.MainWindowHandle, 9)  # SW_RESTORE
```

Save as `.ps1` and execute via `-File` (do NOT use inline with `$_` in git-bash).

### 4. URLs Type Garbled in Browser

**Symptoms:**
- Typing a URL produces wrong characters
- Browser redirects to search instead of the URL

**Causes:**
- Active keyboard layout is not English-US (e.g., Cyrillic, Polish)

**Fixes:**
1. **Best:** Use `set_value` on the address bar element (bypasses keyboard layout)
2. **Good:** Use clipboard paste: PowerShell `Set-Clipboard` then `Ctrl+V`
3. **Workaround:** Ask user to paste the URL manually (they can switch layouts)

### 5. Save As Dialog Not Responding

**Symptoms:**
- Background clicks on Save As dialog fail
- Error: "Background delivery not available for target window class Chrome_WidgetWin_1"

**Fixes:**
1. Use MCP computer_use tool (mouse moves at OS level)
2. Use keyboard accelerator: `Alt+<accelerator key>` (Alt+S for English, Alt+Z for Polish)

### 6. Skill Not Found

**Symptoms:**
- `hermes skills list` doesn't show the skill

**Fixes:**
1. Verify installation: `ls ~/.hermes/skills/windows-computer-use/SKILL.md`
2. Reinstall: `bash scripts/install.sh`
3. Ensure Hermes version ≥ 0.7.0

## Diagnostic Commands

```bash
# Hermes health check
hermes doctor
hermes computer-use doctor

# cua-driver diagnostics
cua-driver config
cua-driver status
cua-driver call get_screen_size

# Window listing
cua-driver call list_windows

# Chrome CDP (if running)
curl -s http://localhost:9222/json/version
```

## Getting Help

1. Check this troubleshooting guide
2. Open a GitHub issue with:
   - Hermes version (`hermes --version`)
   - Windows version (`winver`)
   - cua-driver version (`cua-driver config`)
   - Steps to reproduce
   - Full error output
