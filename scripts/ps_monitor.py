#!/usr/bin/env python3
"""ps_monitor.py — фоновий монітор запуску powershell.exe
Ловить через WMI події створення процесу, логує:
- час, PID, ім'я процесу
- батьківський процес (PID + ім'я)
- командний рядок
Працює без вікон (CREATE_NO_WINDOW).
"""

import subprocess
import time
import datetime
import json
import sys
import os

LOG_FILE = r"C:\hermes_work\ps_monitor.log"
PID_FILE = r"C:\hermes_work\ps_monitor.pid"

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_process_info(pid):
    """Get process name and command line by PID"""
    r = subprocess.run(
        f'wmic process where "processid={pid}" get name,commandline /FORMAT:CSV 2>nul',
        capture_output=True, timeout=5, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    out = r.stdout.decode('cp1252', errors='replace')
    for line in out.split('\n')[1:]:
        parts = [p.strip('" ') for p in line.split(',')]
        if len(parts) >= 2:
            return parts[0], parts[1] if len(parts) > 1 else ''
    return 'unknown', ''

def get_parent_name(pid):
    """Find parent PID and its name"""
    r = subprocess.run(
        f'wmic process where "processid={pid}" get parentprocessid /FORMAT:CSV 2>nul',
        capture_output=True, timeout=5, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    out = r.stdout.decode('cp1252', errors='replace')
    for line in out.split('\n')[1:]:
        ppid = line.strip().strip('" ')
        if ppid.isdigit():
            ppid = int(ppid)
            pname, pcmd = get_process_info(ppid)
            return ppid, pname, pcmd[:150]
    return 0, 'unknown', ''

# Save PID
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

log("=" * 60)
log("ps_monitor STARTED")
log(f"PID: {os.getpid()}")
log(f"Ловлю: powershell.exe, WindowsTerminal.exe")
log("=" * 60)

# Polling approach (WMI events require win32com which may not be available)
# Poll every 2 seconds for new powershell processes
known_pids = set()

while True:
    try:
        for proc in ['powershell.exe', 'WindowsTerminal.exe']:
            r = subprocess.run(
                f'wmic process where "name=\'{proc}\'" get processid /FORMAT:CSV 2>nul',
                capture_output=True, timeout=5, shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            out = r.stdout.decode('cp1252', errors='replace')
            for line in out.split('\n')[1:]:
                pid_str = line.strip().strip('" ')
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid not in known_pids:
                        known_pids.add(pid)
                        name, cmdline = get_process_info(pid)
                        ppid, pname, pcmd = get_parent_name(pid)
                        log(f"🚨 НОВИЙ ПРОЦЕС: {proc}")
                        log(f"   PID: {pid}")
                        log(f"   CMD: {cmdline[:200]}")
                        log(f"   БАТЬКО: {pname} (PID {ppid})")
                        log(f"   БАТЬКО CMD: {pcmd}")

        # Also clean dead PIDs occasionally (keep last 100)
        if len(known_pids) > 500:
            known_pids = set(list(known_pids)[-250:])

        time.sleep(2)

    except KeyboardInterrupt:
        log("ps_monitor STOPPED (Ctrl+C)")
        break
    except Exception as e:
        log(f"ПОМИЛКА: {e}")
        time.sleep(5)
