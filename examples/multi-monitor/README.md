# Multi-Monitor Configuration Guide

## Overview

This guide provides examples for configuring and troubleshooting multi-monitor setups with Hermes Agent's `computer_use` tool on Windows.

## Detecting Monitor Layout

```powershell
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens |
    Select-Object DeviceName, Bounds, WorkingArea, Primary | Format-List
```

### Example Output

```
DeviceName : \\.\DISPLAY1
Bounds     : {X=0, Y=0, Width=1920, Height=1080}
WorkingArea: {X=0, Y=0, Width=1920, Height=1040}
Primary    : True

DeviceName : \\.\DISPLAY2
Bounds     : {X=1920, Y=0, Width=1080, Height=1920}
WorkingArea: {X=1920, Y=0, Width=1080, Height=1880}
Primary    : False
```

## Common Layouts

### Landscape + Portrait

```
DISPLAY1 (primary): 1920x1080 at (0, 0) — landscape
DISPLAY2: 1080x1920 at (1920, 0) — portrait (rotated)
```

Click targets:
- Primary: X ∈ [0, 1919], Y ∈ [0, 1079]
- Secondary: X ∈ [1920, 2999], Y ∈ [0, 1919]

### Dual Landscape

```
DISPLAY1 (primary): 1920x1080 at (0, 0)
DISPLAY2: 1920x1080 at (1920, 0)
```

Click targets:
- Primary: X ∈ [0, 1919], Y ∈ [0, 1079]
- Secondary: X ∈ [1920, 3839], Y ∈ [0, 1079]

## Bringing Apps to the Primary Monitor

Tell the user to press: **`Win + Shift + ←`**

This moves the active window to the primary monitor without affecting size.

## Troubleshooting

### Capture Returns Only Primary Monitor

The cua-driver only captures the foreground window or primary monitor. To see a secondary monitor, use:

```python
computer_use(action="capture", app="AppName")
```

This captures a specific app window regardless of which monitor it's on.

### SOM Elements Span All Monitors

Even though the screenshot shows only the primary monitor, SOM element indices work across all monitors. Clicking element 14 may land on the secondary monitor if that's where the element actually is.
