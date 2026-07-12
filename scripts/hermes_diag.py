#!/usr/bin/env python3
"""hermes_diag.py — Сценарій дій при системних проблемах
Використання: python C:\hermes_work\hermes_diag.py [check|fix|report]

Діагностує та виправляє:
- Gateway не відповідає / restart loop
- computer_use / MCP не бачить екран
- VS Code zombie процеси
- PowerShell вікна під час фонових процесів
- WSL1 не стартує
- Високе RAM/CPU
"""

import subprocess, os, sys, time, datetime

HERMES_HOME = os.path.expanduser('~/AppData/Local/hermes')
LOG_FILE = r"C:\hermes_work\hermes_diag.log"

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def wmic_decode(output):
    if not output: return ''
    for enc in ['utf-16-le', 'cp1252', 'utf-8']:
        try: return output.decode(enc, errors='replace').strip()
        except: pass
    return ''

def get_pids(name):
    r = subprocess.run(
        f'wmic process where name="{name}" get processid /FORMAT:CSV 2>nul',
        capture_output=True, timeout=5, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    out = wmic_decode(r.stdout)
    return [l.strip().strip('" ') for l in out.split('\n')[1:] if l.strip().strip('" ').isdigit()]

def get_cmd(pid):
    r = subprocess.run(
        f'wmic process where "processid={pid}" get commandline /FORMAT:CSV 2>nul',
        capture_output=True, timeout=5, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return wmic_decode(r.stdout)

# ============================================================
def check_gateway():
    log("\n=== Gateway ===")
    pids = get_pids('pythonw.exe')
    gw_pids = []
    for pid in pids:
        cmd = get_cmd(pid)
        if 'gateway' in cmd.lower():
            gw_pids.append(pid)
    if gw_pids:
        log(f"✅ Gateway PID {','.join(gw_pids)}")
        r = subprocess.run(
            f'wmic process where "processid={gw_pids[0]}" get WorkingSetSize /VALUE 2>nul',
            capture_output=True, timeout=5, shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in wmic_decode(r.stdout).split('\n'):
            if 'WorkingSetSize' in line:
                try: log(f"   RAM: {int(line.split('=')[1])/1048576:.0f} MB")
                except: pass
        return True
    log("❌ Gateway NIE DZIAŁA")
    return False

def fix_gateway():
    log("🛠️ Restart Gateway...")
    pids = get_pids('pythonw.exe')
    for pid in pids:
        cmd = get_cmd(pid)
        if 'gateway' in cmd.lower():
            subprocess.run(['taskkill', '/F', '/PID', pid],
                          capture_output=True, timeout=5,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            log(f"   PID {pid} killed")
    time.sleep(2)
    subprocess.run('schtasks /Run /TN "Hermes_Gateway" 2>nul',
                  capture_output=True, timeout=15, shell=True,
                  creationflags=subprocess.CREATE_NO_WINDOW)
    log("⏳ Gateway uruchamianie... (sprawdź Telegram za 10s)")
    time.sleep(5)
    if check_gateway():
        log("✅ Gateway uruchomiony")
    else:
        log("❌ Gateway nie wstał — potrzebny restart komputera")

# ============================================================
def check_mcp():
    log("\n=== MCP computer-use-mcp ===")
    node_pids = get_pids('node.exe')
    mcp_node = [p for p in node_pids if 'computer-use' in get_cmd(p).lower()]
    
    electron_pids = get_pids('electron.exe')
    mcp_el = [p for p in electron_pids if 'computer-use' in get_cmd(p).lower()]
    
    if mcp_node: log(f"✅ Node server PID {mcp_node[0]}")
    else: log("❌ Node server NIE DZIAŁA")
    
    if mcp_el: log(f"✅ Electron overlay: {len(mcp_el)} proc.")
    else: log("❌ Electron overlay NIE DZIAŁA")
    return mcp_node and mcp_el

# ============================================================
def check_zombies():
    """Znajdź wszystkie zombie procesy — GUI apps bez okna"""
    log("\n=== Zombie procesy ===")
    
    # Lista GUI aplikacji do sprawdzenia
    gui_apps = {
        'Code.exe': 'Visual Studio Code',
        'chrome.exe': 'Google Chrome',
        'firefox.exe': 'Mozilla Firefox',
        'brave.exe': 'Brave Browser',
        'opera.exe': 'Opera Browser',
        'explorer.exe': 'File Explorer',
        'Notepad++.exe': 'Notepad++',
        'WINWORD.EXE': 'Microsoft Word',
        'EXCEL.EXE': 'Microsoft Excel',
        'POWERPNT.EXE': 'Microsoft PowerPoint',
        'OUTLOOK.EXE': 'Microsoft Outlook',
        'Telegram.exe': 'Telegram',
        'Discord.exe': 'Discord',
        'Slack.exe': 'Slack',
        'obs64.exe': 'OBS Studio',
        'Spotify.exe': 'Spotify',
    }
    
    zombies = []
    for exe, name in gui_apps.items():
        pids = get_pids(exe)
        if not pids:
            continue
        
        # Sprawdź czy któryś ma okno
        has_window = False
        for pid in pids[:3]:
            r = subprocess.run(
                'powershell.exe -NoProfile -WindowStyle Hidden -Command '
                f'"$p=Get-Process -Id {pid} -EA 0; if($p -and $p.MainWindowHandle -ne 0){{Write-Output 1}}else{{Write-Output 0}}"',
                capture_output=True, timeout=10, shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if '1' in r.stdout.decode('cp1252', errors='replace'):
                has_window = True
                break
        
        if not has_window and pids:
            zombies.append((exe, name, pids))
    
    if zombies:
        log(f"⚠️ Znaleziono {len(zombies)} zombie proces(ów):")
        for exe, name, pids in zombies:
            log(f"   • {name} ({exe}) — {len(pids)} proc., PID: {','.join(pids[:5])}")
        return zombies
    else:
        log("✅ Brak zombie procesów")
        return []

def fix_zombies(zombies=None):
    """Zabij wszystkie zombie procesy"""
    if zombies is None:
        zombies = check_zombies()
    
    if not zombies:
        log("✅ Brak zombie do zabicia")
        return
    
    log(f"🛠️ Zabijam {len(zombies)} zombie...")
    killed = set()
    for exe, name, pids in zombies:
        if exe not in killed:
            subprocess.run(['taskkill', '/F', '/IM', exe],
                          capture_output=True, timeout=10,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            killed.add(exe)
            log(f"   💀 {name} ({exe}) — wszystkie procesy zabite")
    
    # Sprawdź czy zostały
    remaining = check_zombies()
    if remaining:
        log("⚠️ Niektóre zombie nie chcą umrzeć — potrzebny restart")
    else:
        log("✅ Wszystkie zombie wyeliminowane")

# ============================================================
def check_wsl():
    log("\n=== WSL ===")
    r = subprocess.run('wsl -l -v 2>&1', capture_output=True, timeout=15, shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
    out = wmic_decode(r.stdout)
    if 'Ubuntu' in out and 'Running' in out:
        log("✅ Ubuntu-26.04 — Running (WSL1)")
        return True
    elif 'Ubuntu' in out:
        log(f"⚠️ Ubuntu-26.04 — Stopped")
        log("   Uruchom: wsl -d Ubuntu-26.04")
        return False
    log(f"❌ WSL: {out[:100]}")
    return False

# ============================================================
def check_resources():
    log("\n=== Zasoby ===")
    r = subprocess.run('wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /VALUE 2>nul',
                      capture_output=True, timeout=5, shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
    out = wmic_decode(r.stdout)
    free = total = 0
    for line in out.split('\n'):
        if 'FreePhysicalMemory' in line: free = int(line.split('=')[1]) / 1024
        if 'TotalVisibleMemorySize' in line: total = int(line.split('=')[1]) / 1024
    if total:
        pct = (1 - free/total) * 100
        log(f"RAM: {free:.0f}MB free / {total:.0f}MB ({pct:.0f}%)")
        if pct > 85: log("⚠️ Wysokie użycie RAM!")

    r2 = subprocess.run('wmic LogicalDisk where "DeviceID=\'C:\'" get FreeSpace,Size /VALUE 2>nul',
                       capture_output=True, timeout=5, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    out2 = wmic_decode(r2.stdout)
    for line in out2.split('\n'):
        if 'FreeSpace' in line:
            log(f"Dysk C: {int(line.split('=')[1])//1073741824}GB free")

# ============================================================
def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'check'
    
    log("=" * 50)
    log(f"HERMES DIAG — {action.upper()}")
    log(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 50)
    
    if action == 'check':
        check_gateway()
        check_mcp()
        check_zombies()
        check_wsl()
        check_resources()
        log("\n💡 Python C:\\hermes_work\\hermes_diag.py fix — naprawa zombie")
    
    elif action == 'fix':
        if not check_gateway(): fix_gateway()
        zombies = check_zombies()
        if zombies: fix_zombies(zombies)
        log("\n✅ Naprawa zakończona. Jeśli problem nadal występuje → restart")
    
    elif action == 'report':
        check_gateway()
        check_mcp()
        check_zombies()
        check_wsl()
        check_resources()

if __name__ == '__main__':
    main()
