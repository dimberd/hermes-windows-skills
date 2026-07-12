# Electron Window Management

## Overview

Electron apps (VS Code, Discord, Slack, Teams) use `Chrome_WidgetWin_1` window class which has specific limitations with background automation.

## The Problem

Background keyboard shortcuts (PostMessage via cua-driver) do NOT change Electron window state. The accessibility tree may report updated bounds but the visual window position stays unchanged.

## The Solution: PowerShell Win32 API

`ShowWindowAsync` works for ALL window types — Electron, Win32, WPF.

### Full Script

```powershell
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class WinAPI {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
}
'@
$proc = Get-Process "Code" -EA 0 | Select-Object -First 1
if ($proc) {
    [WinAPI]::ShowWindowAsync($proc.MainWindowHandle, 9)  # SW_RESTORE
    Start-Sleep -Milliseconds 200
    [WinAPI]::ShowWindowAsync($proc.MainWindowHandle, 3)  # SW_MAXIMIZE
    [WinAPI]::SetForegroundWindow($proc.MainWindowHandle)
    [WinAPI]::BringWindowToTop($proc.MainWindowHandle)
}
```

### Calling from Python (within Hermes)

```python
# Save as .ps1 and execute
terminal(
    command='powershell -ExecutionPolicy Bypass -File "C:\\path\\to\\restore.ps1" Code',
    timeout=15
)
```

## Detection Logic

After capture:
- **≤5 elements** → window is minimized (only title bar buttons visible)
- **Many elements** → window is active

## What Does NOT Work

| Method | Result |
|--------|--------|
| Alt+Tab via cua-driver | ❌ Not processed by shell |
| F11 key press | ❌ Electron ignores background keys |
| Win+Up | ❌ Goes to shell, not the window |
| Click Maximize button | ❌ UIA reports OK but no visual change |
| Win+D | ❌ "Unknown key: d" |
| Alt+Space menu | ❌ System menu doesn't respond |
