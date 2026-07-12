#!/usr/bin/env python3
"""proc_watchdog.py — слідкує за процесами, не дає плодити фейкові копії
Ловить: дублікати GUI програм, процеси без вікон, аномальну кількість інстанцій.

Правила:
- VS Code: максимум 1 main + здорові діти (≤15 total, 1 видиме вікно)
- Якщо main процес є, а вікна нема — значить фейковий → вбити
- Логує всі підозрілі події
"""

import subprocess, time, datetime, os, json, sys

LOG_FILE = r"C:\hermes_work\proc_watchdog.log"
PID_FILE = r"C:\hermes_work\proc_watchdog.pid"
SPAWN_LOG = r"C:\hermes_work\proc_watchdog_spawns.json"

# Програми, за якими слідкуємо особливо
WATCHED_APPS = {
    'Code.exe': {
        'max_total': 15, 'max_main': 1,
        'description': 'Visual Studio Code',
        'needs_window': True,
    },
    'electron.exe': {
        'max_total': 10, 'max_main': 1,
        'description': 'MCP Electron overlay',
        'needs_window': False,
    },
    'node.exe': {
        'max_total': 5, 'max_main': 1,
        'description': 'MCP Node server',
        'needs_window': False,
    },
    # GUI apps — sprawdzaj czy mają okno (zombie detection)
    'chrome.exe': {'max_total': 50, 'max_main': 1, 'description': 'Chrome', 'needs_window': True},
    'firefox.exe': {'max_total': 30, 'max_main': 1, 'description': 'Firefox', 'needs_window': True},
    'WINWORD.EXE': {'max_total': 5, 'max_main': 1, 'description': 'Word', 'needs_window': True},
    'EXCEL.EXE': {'max_total': 5, 'max_main': 1, 'description': 'Excel', 'needs_window': True},
    'Telegram.exe': {'max_total': 5, 'max_main': 1, 'description': 'Telegram', 'needs_window': True},
}

def get_processes(app_name):
    """Get all instances of a process with PIDs"""
    r = subprocess.run(
        f'wmic process where "name=\'{app_name}\'" get processid /FORMAT:CSV 2>nul',
        capture_output=True, timeout=5, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    out = r.stdout.decode('cp1252', errors='replace')
    pids = []
    for line in out.split('\n')[1:]:
        pid = line.strip().strip('" ')
        if pid.isdigit():
            pids.append(int(pid))
    return pids

def has_visible_window(pid):
    """Check if a process has at least one visible window"""
    r = subprocess.run(
        f'powershell.exe -NoProfile -WindowStyle Hidden -Command '
        f'"Add-Type @\\\"using System;using System.Runtime.InteropServices;'
        f'public class W {{ [DllImport(\\\"user32.dll\\\")] public static extern bool EnumWindows(Delegate d, int p);'
        f'[DllImport(\\\"user32.dll\\\")] public static extern bool IsWindowVisible(IntPtr h);'
        f'[DllImport(\\\"user32.dll\\\")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid); }};'
        f'$found=$false;'
        f'[W]::EnumWindows([Func[IntPtr,IntPtr,bool]]{{param($h,$l)'
        f'if([W]::IsWindowVisible($h)){{$p=0;[W]::GetWindowThreadProcessId($h,[ref]$p);'
        f'if($p -eq {pid}){{$found=$true;return $false}}}};$true}},0);'
        f'Write-Output $found\"',
        capture_output=True, timeout=10, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    out = r.stdout.decode('cp1252', errors='replace').strip().lower()
    return 'true' in out

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_spawn(app_name, pid, method):
    """Track processes we spawn"""
    spawns = {}
    if os.path.exists(SPAWN_LOG):
        try:
            with open(SPAWN_LOG, 'r') as f:
                spawns = json.load(f)
        except:
            pass
    spawns[str(pid)] = {
        'app': app_name,
        'method': method,
        'time': datetime.datetime.now().isoformat(),
    }
    with open(SPAWN_LOG, 'w') as f:
        json.dump(spawns, f, indent=2)

def cleanup_watched(app_config, app_name):
    """Check and clean up a watched application"""
    pids = get_processes(app_name)
    total = len(pids)
    
    if total == 0:
        return
    
    config = app_config
    max_total = config.get('max_total', 20)
    max_main = config.get('max_main', 1)
    needs_window = config.get('needs_window', False)
    desc = config.get('description', app_name)
    
    # Check if too many total processes
    if total > max_total:
        log(f"⚠️ {desc}: {total} процесів (макс {max_total}) — ВБИВАЮ ВСІ")
        for pid in pids:
            subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                          capture_output=True, timeout=5,
                          creationflags=subprocess.CREATE_NO_WINDOW)
        log(f"💀 {desc}: вбито {total} процесів (перевищення ліміту)")
        return
    
    # Check if main process has no window
    if needs_window and total > 0:
        # Check EACH process for a visible window - not just the first
        any_window = False
        for pid in pids:
            if has_visible_window(pid):
                any_window = True
                break
        
        if not any_window:
            log(f"⚠️ {desc}: ЖОДЕН з {total} процесів не має вікна — ВБИВАЮ ВСІ (блокують користувача)")
            subprocess.run(['taskkill', '/F', '/IM', app_name],
                          capture_output=True, timeout=5,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            log(f"💀 {desc}: вбито {total} фейкових процесів (без вікна — блокують реальний запуск)")
            return
    
    # Check for multiple main instances
    if total > max_main * 3:  # heuristic: if there are many more processes than expected
        log(f"⚠️ {desc}: {total} процесів — можливі дублікати, вбиваю всі")
        subprocess.run(['taskkill', '/F', '/IM', app_name],
                      capture_output=True, timeout=5,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        log(f"💀 {desc}: вбито {total} процесів (аномальна кількість)")

# Save PID
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

log("=" * 60)
log("PROC_WATCHDOG STARTED")
log(f"PID: {os.getpid()}")
log(f"Стежу за: {', '.join(WATCHED_APPS.keys())}")
log("=" * 60)

# Also clean spawn log on restart
if os.path.exists(SPAWN_LOG):
    os.remove(SPAWN_LOG)

# Export clean function for external use
def clean_all():
    """External API: clean all watched apps"""
    results = {}
    for app_name, config in WATCHED_APPS.items():
        cleanup_watched(config, app_name)
        results[app_name] = "checked"
    return results

cycle = 0
while True:
    try:
        cycle += 1
        for app_name, config in WATCHED_APPS.items():
            cleanup_watched(config, app_name)
        
        if cycle % 30 == 0:  # log health every ~1 min
            for app_name in WATCHED_APPS:
                pids = get_processes(app_name)
                log(f"ℹ️ {app_name}: {len(pids)} процесів")
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        log("PROC_WATCHDOG STOPPED (Ctrl+C)")
        break
    except Exception as e:
        log(f"ПОМИЛКА: {e}")
        time.sleep(10)
