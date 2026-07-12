#!/usr/bin/env python3
"""Моніторинг Denisboss — перевіряє доступність і критичні вимкнення"""
import subprocess, os, sys, json, datetime, re

script_dir = os.path.dirname(os.path.abspath(__file__))
# Пробуємо різні варіанти шляхів (git-bash / WSL / native Windows)
BASE = os.environ.get('HERMES_WORK', '')
if BASE and os.path.exists(BASE):
    pass  # використовуємо змінну середовища
elif os.path.exists('/c/hermes_work/secure'):
    BASE = '/c/hermes_work/secure'
elif os.path.exists('/mnt/c/hermes_work/secure'):
    BASE = '/mnt/c/hermes_work/secure'
elif os.path.exists(r'C:\hermes_work\secure'):
    BASE = r'C:\hermes_work\secure'
else:
    BASE = script_dir  # fallback

KEY = os.path.join(BASE, 'brother_ssh_key')
HOST = '100.116.175.36'
USER = 'denis_boss'
STATE = os.path.join(BASE, 'denisboss_state.json')

def ssh(cmd):
    try:
        r = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=accept-new',
             '-i', KEY, f'{USER}@{HOST}', cmd],
            capture_output=True, text=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return None, -1
    except Exception as e:
        return str(e), -2

def load_state():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {'last_count': 0, 'last_seen': None, 'offline_since': None}

def save_state(s):
    with open(STATE, 'w') as f:
        json.dump(s, f)

# 1. Перевіряємо чи хост доступний (ping)
ping_r = subprocess.run(['ping', '-n', '1', '-w', '3000', HOST],
                        capture_output=True, text=True, timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW)

state = load_state()
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if ping_r.returncode != 0:
    # Хост недоступний
    if state.get('offline_since') is None:
        state['offline_since'] = now
        save_state(state)
    print(f'❌ DENISBOSS OFFLINE — з {state["offline_since"]}')
    sys.exit(0)

# 2. Хост доступний — виконуємо PowerShell
ps_out, rc = ssh(
    'powershell -Command "'
    '$e=Get-WinEvent -FilterHashtable @{LogName=\\"System\\";Id=41} -MaxEvents 10 -ErrorAction SilentlyContinue;'
    'if($e){$c=$e.Count;$t=$e[0].TimeCreated.ToString(\\"yyyy-MM-dd HH:mm:ss\\");'
    'Write-Output \\"COUNT:$c|FIRST:$t\\";'
    '$e|%{$_.TimeCreated.ToString(\\"yyyy-MM-dd HH:mm:ss\\")}}'
    'else{Write-Output \\"COUNT:0\\"}"'
)

if rc != 0 or ps_out is None:
    print(f'⚠️ SSH FAILED — {now}')
    sys.exit(1)

# Парсимо результат
count = 0
first_time = 'none'
events = []
for line in ps_out.split('\n'):
    line = line.strip()
    if line.startswith('COUNT:'):
        m = re.match(r'COUNT:(\d+)(?:\|FIRST:(.*))?', line)
        if m:
            count = int(m.group(1))
            first_time = m.group(2) or 'none'
    elif line and not line.startswith('#') and not line.startswith('<'):
        events.append(line)

# Якщо був офлайн — пишемо коли повернувся
msg_parts = []
if state.get('offline_since'):
    msg_parts.append(f'🟢 Повернувся після офлайн: {state["offline_since"]} → {now}')
    state['offline_since'] = None

# Нові критичні події?
if count == 0:
    msg_parts.append(f'✅ Стабільно — критичних вимкнень немає ({now})')
elif count > state.get('last_count', 0):
    new_events = count - state['last_count']
    msg_parts.append(f'🔴 НОВІ КРИТИЧНІ ВИМКНЕННЯ: +{new_events} (всього: {count})')
    msg_parts.append(f'Останнє: {first_time}')
    msg_parts.append('Час подій:')
    for e in events[:5]:
        msg_parts.append(f'  • {e}')
    if count != state.get('last_count'):
        state['last_count'] = count
        state['last_seen'] = now
else:
    msg_parts.append(f'ℹ️ Критичних вимкнень: {count} (без змін)')

save_state(state)
print('\n'.join(msg_parts))
