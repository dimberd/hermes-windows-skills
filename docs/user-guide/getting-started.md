# Getting Started with Hermes Windows Skills

## Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com) installed (≥ v0.7.0)
- Windows 10/11 with PowerShell 5.1+
- git-bash (comes with Git for Windows) or MSYS2

## Installation

### Automatic Installation

```bash
git clone https://github.com/<your-org>/hermes-windows-skills.git
cd hermes-windows-skills
bash scripts/install.sh
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/<your-org>/hermes-windows-skills.git

# Copy skills
cp -r hermes-windows-skills/skills/* ~/.hermes/skills/

# Verify
hermes skills list | grep windows
```

### Using a Specific Profile

```bash
bash scripts/install.sh --profile work
```

## Loading Skills

### Preload at Session Start

```bash
hermes -s windows-computer-use
```

### Load During Session

```
/skill windows-computer-use
```

## Verifying Installation

```bash
# List installed skills
hermes skills list

# Load and query
hermes -s windows-computer-use -q "Show me the multi-monitor setup steps"
```

## Quick Examples

### Check Monitor Configuration

Query the skill:

```
/skill windows-computer-use
Show me how to detect my monitor layout.
```

### Restore a Minimized Electron Window

```powershell
Add-Type @'
using System; using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h, int n);
}
'@
$p = Get-Process "Code" -EA 0 | Select-Object -First 1
[W]::ShowWindowAsync($p.MainWindowHandle, 9)
```

### Check cua-driver Health

```bash
cua-driver doctor
cua-driver config
```

## Updating

```bash
cd hermes-windows-skills
git pull
bash scripts/install.sh
```

## Uninstalling

```bash
cd hermes-windows-skills
bash scripts/uninstall.sh
```

## Troubleshooting

See `troubleshooting.md` or run the skill's built-in troubleshooting:

```
/skill windows-computer-use
Troubleshoot: capture returns 0x0
```
