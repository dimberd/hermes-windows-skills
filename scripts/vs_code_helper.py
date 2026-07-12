"""vs_code_helper.py — безпечний запуск VS Code без дублікатів
Використання: from vs_code_helper import safe_launch_vscode
             safe_launch_vscode('D:\\Sorb\\projekty\\hermes-windows-skills')

Правила:
- Перевіряє чи вже є живий VS Code з видимим вікном
- Якщо є — просто фокусує його (через computer-use-mcp)
- Якщо нема — запускає через os.startfile (правильний Windows спосіб)
- Якщо є фейковий (процес без вікна) — вбиває і запускає наново
"""

import subprocess, os, time

VSCODE_PATH = r"C:\Users\PL_home\AppData\Local\Programs\Microsoft VS Code\Code.exe"

def _get_code_pids():
    """Get all Code.exe PIDs"""
    r = subprocess.run(
        'wmic process where "name=\'Code.exe\'" get processid /FORMAT:CSV 2>nul',
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

def _has_visible_window_simple():
    """Quick check: does any Code window exist?"""
    r = subprocess.run(
        'powershell.exe -NoProfile -WindowStyle Hidden -Command '
        '"$w=get-process code -EA 0; if(-not $w){Write-Output false;exit} '
        '$s=(Get-Process code | Where-Object {$_.MainWindowHandle -ne 0}); '
        'if($s){Write-Output true}else{Write-Output false}"',
        capture_output=True, timeout=10, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    out = r.stdout.decode('cp1252', errors='replace').strip().lower()
    return 'true' in out

def safe_launch_vscode(folder=None):
    """
    Безпечний запуск VS Code.
    Повертає dict: {'status': 'ok'|'focused'|'killed_and_launched'|'error', 'detail': str}
    """
    pids = _get_code_pids()
    
    if pids:
        # VS Code вже є — перевіряємо чи вікно видиме
        has_window = _has_visible_window_simple()
        
        if has_window:
            return {'status': 'ok', 'detail': f'VS Code вже працює (PID {pids[0]})'}
        else:
            # Фейковий процес — вбиваємо
            print(f"⚠️ Фейковий VS Code: {len(pids)} процесів без вікна. Вбиваю...")
            subprocess.run(['taskkill', '/F', '/IM', 'Code.exe'],
                          capture_output=True, timeout=10,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)
            
            # Запускаємо справжній
            if folder:
                os.startfile(folder)
            else:
                os.startfile(VSCODE_PATH)
            
            time.sleep(2)
            new_pids = _get_code_pids()
            return {'status': 'killed_and_launched', 
                    'detail': f'Вбито {len(pids)} фейкових, запущено новий. PID: {new_pids}'}
    else:
        # VS Code не запущений — запускаємо
        if folder:
            # subprocess BEZ creationflags — GUI musi mieć okno!
            subprocess.Popen([VSCODE_PATH, folder], close_fds=True)
        else:
            subprocess.Popen([VSCODE_PATH], close_fds=True)
        
        time.sleep(3)
        new_pids = _get_code_pids()
        if _has_visible_window_simple():
            return {'status': 'launched', 'detail': f'VS Code запущено z oknem. PID: {new_pids}'}
        else:
            # Fallback: user otworzy ręcznie
            return {'status': 'no_window', 'detail': f'Proces jest (PID {new_pids}) ale okno niewidoczne. Otwórz ręcznie.'}
