# Remote Windows Diagnostics via SSH

> A guide to performing comprehensive diagnostics on remote Windows PCs via Tailscale SSH, using PowerShell, Sysinternals, and Hermes Agent cron monitoring.

## Overview

This guide covers:

- Remote diagnostics via SSH for Windows 10/11
- Sysinternals Suite installation and CLI usage
- Event Log analysis for unexpected shutdowns and BSOD
- Disk health (S.M.A.R.T.) monitoring
- Automated cron-based uptime monitoring
- Power management for always-on remote access

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Remote PC | Windows 10/11 with OpenSSH Server installed |
| Network | Tailscale or VPN connection (direct IP reachable) |
| SSH Key | ED25519 key pair, public key added to remote PC |
| Hermes Agent | ≥ 0.7.0 with `computer_use` and `terminal` tools |

---

## Installation

### 1. Install Sysinternals Suite on Remote PC

```powershell
# One-command installation
curl.exe -sL "https://download.sysinternals.com/files/SysinternalsSuite.zip" -o "$env:TEMP\Sysinternals.zip"
Expand-Archive "$env:TEMP\Sysinternals.zip" -DestinationPath "C:\Tools\Sysinternals" -Force

# Add to system PATH (run as Administrator)
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Tools\Sysinternals", "Machine")
```

### Key CLI Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `autorunsc.exe` | Analyze startup entries (services, tasks, drivers) | `autorunsc64.exe -a * -c -m -s` |
| `psloglist.exe` | Dump Event Log with filters | `psloglist -s -d 1 System` |
| `handle64.exe` | Find which process has a file locked | `handle64.exe -a filename` |
| `psfile.exe` | List files opened remotely | `psfile.exe` |

### 2. Copy Diagnostic Script to Remote PC

```bash
# Using SCP
scp -i ~/.ssh/key scripts/denisboss_diag.ps1 user@100.x.x.x:~/diag.ps1

# Execute
ssh -i ~/.ssh/key user@100.x.x.x "powershell -ExecutionPolicy Bypass -File ~/diag.ps1"
```

---

## Diagnostic Checks

### Unexpected Shutdowns (Kernel-Power 41)

```powershell
# All unexpected shutdowns
Get-WinEvent -FilterHashtable @{LogName="System"; Id=41} -MaxEvents 50 | 
    Format-Table TimeCreated, Id -AutoSize

# Count
$count = (Get-WinEvent -FilterHashtable @{LogName="System"; Id=41} -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "Unexpected shutdowns: $count"
```

### Shutdown History (Event 1074)

```powershell
Get-WinEvent -FilterHashtable @{LogName="System"; Id=1074} -MaxEvents 30 | ForEach-Object {
    $m = $_.Message
    $user = if ($m -match "on behalf of user (.+?) for") { $matches[1] } else { "?" }
    Write-Host "$($_.TimeCreated) | user: $user"
}
```

### BSOD / Windows Error Reporting

```powershell
Get-WinEvent -FilterHashtable @{LogName="Application"; Id=1001} -MaxEvents 20 |
    Format-Table TimeCreated, Message -AutoSize -Wrap
```

### Minidump Files

```powershell
Get-ChildItem "C:\Windows\Minidump" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object LastWriteTime, Name, @{N="Size(KB)";E={[math]::Round($_.Length/1KB,1)}}
```

### Disk S.M.A.R.T. Health

```powershell
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Size, HealthStatus, OperationalStatus

# Logical disk usage
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    [PSCustomObject]@{
        Disk = $_.DeviceID
        SizeGB = [math]::Round($_.Size/1GB, 1)
        FreeGB = [math]::Round($_.FreeSpace/1GB, 1)
        FreePct = [math]::Round($_.FreeSpace/$_.Size*100, 1)
    }
}
```

### WHEA Hardware Errors

```powershell
Get-WinEvent -FilterHashtable @{LogName="System"; ProviderName="Microsoft-Windows-WHEA-Logger"} -MaxEvents 20
```

### Reliability Monitor

```powershell
Get-WinEvent -FilterHashtable @{
    LogName="Microsoft-Windows-Diagnostics-Performance/Operational"
    Id=100,101,200,201
} -MaxEvents 30
```

---

## Automated Cron Monitoring

Create a Hermes cron job that checks the remote PC every 10 minutes:

```bash
hermes cron create \
  --name "Remote PC Monitor" \
  --schedule "every 10m" \
  --script denisboss_monitor.py \
  --no-agent
```

The script (`denisboss_monitor.py`):
- Pings the remote PC every 10 minutes
- Records offline time when the PC is unreachable
- When the PC comes back online, checks for new Kernel-Power 41 events
- Sends alerts when new unexpected shutdowns are detected

### View Status

```bash
hermes cron list
hermes cron logs --job-id <job-id>
```

---

## Power Management

For a remote PC that must stay accessible 24/7:

```powershell
# Never sleep
powercfg /CHANGE standby-timeout-ac 0
powercfg /CHANGE standby-timeout-dc 0

# Never hibernate
powercfg /CHANGE hibernate-timeout-ac 0
powercfg /CHANGE hibernate-timeout-dc 0
powercfg /H OFF

# Never turn off disks
powercfg /CHANGE disk-timeout-ac 0
powercfg /CHANGE disk-timeout-dc 0

# Monitor off after 10 minutes (wake on mouse/keyboard)
powercfg /CHANGE monitor-timeout-ac 10
powercfg /CHANGE monitor-timeout-dc 10

# Disable USB selective suspend
powercfg /SETACVALUEINDEX SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0

# Disable NIC power saving (requires admin)
Get-NetAdapter -Physical | Where-Object { $_.Status -eq "Up" } | Disable-NetAdapterPowerManagement
```

---

## Troubleshooting

### SSH Connection Timing Out

| Cause | Check | Fix |
|-------|-------|-----|
| Kaspersky firewall blocking | Run the power management script first | Add sshd.exe to trusted apps |
| Incorrect authorized_keys permissions | `icacls %USERPROFILE%\.ssh\authorized_keys` | Set only `SYSTEM:(F)` + `user:(R)` |
| Wrong username | `ssh user@ip` where user ≠ login | Use correct local username |
| PC is sleeping | Power plan not applied | Re-apply powercfg settings |

### Diagnostic Script Not Running via SCP

If SCP fails with "No such file or directory", the remote Desktop path may contain non-ASCII characters. Use PowerShell Base64 encoding instead:

```bash
# Encode script content
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\script.ps1"))

# On remote PC, decode and save
$b = [Convert]::FromBase64String("$b64")
[IO.File]::WriteAllBytes("$env:USERPROFILE\script.ps1", $b)
```
