# PowerShell Window Suppression on Windows

> Як запобігти появі вікон PowerShell від фонових процесів Hermes.

## Проблема

Під час роботи Hermes Agent на Windows можуть з'являтися видимі вікна PowerShell з різних джерел:

| Джерело | Причина | Виправлення |
|---------|---------|-------------|
| **computer-use-mcp** | Node.js MCP сервер викликає `powershell.exe` для `focus_window`. Має `windowsHide: true`, але не завжди працює | Оновлення самого пакету, або моніторинг |
| **HermesPostBoot** (Scheduled Task) | Запускає `powershell.exe` без `-WindowStyle Hidden` | Замінити на VBS (`wscript.exe //B //Nologo`) |
| **Hermes Watchdog v2** (Scheduled Task) | Відсутній параметр `-WindowStyle Hidden` | Додати `-WindowStyle Hidden` |
| **hermes_startup.ps1** (Startup folder) | Windows запускає .ps1 у видимому вікні | Замінити на .vbs з `WshShell.Run` style 0 |

## Виправлення

### 1. Startup folder: .ps1 → .vbs

Перейменувати `hermes_startup.ps1` на `_hermes_startup_runner.ps1` і створити `hermes_startup.vbs`:

```vbs
' hermes_startup.vbs — запускає Hermes startup без вікон
Set WshShell = CreateObject("WScript.Shell")
ps1path = "C:\Users\PL_home\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\_hermes_startup_runner.ps1"
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1path & """"
WshShell.Run cmd, 0, False
```

### 2. Scheduled Tasks: додати `-WindowStyle Hidden`

```powershell
schtasks /Change /TN "Hermes Watchdog v2" /TR "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File 'C:\Scripts\Hermes-Watchdog.ps1' -Once -Minimal"
```

Або замінити на VBS:

```powershell
schtasks /Change /TN "HermesPostBoot" /TR "wscript.exe //B //Nologo 'C:\path\to\script.vbs'"
```

### 3. computer-use-mcp: аналіз

`@cypherpotato/computer-use-mcp` (`computerRuntime.js`) викликає PowerShell для `focus_window()`:

```javascript
const { stdout } = await execFileAsync('powershell.exe', 
    ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', script],
    { env, windowsHide: true }
);
```

`windowsHide: true` в Node.js використовує `CREATE_NO_WINDOW` (0x08000000). На деяких конфігураціях Windows це може не спрацювати. 

### 4. Launch VS Code silently

Для запуску VS Code без terminal() — Python з CREATE_NO_WINDOW:

```python
import subprocess
subprocess.Popen(
    ['code', 'D:\\Sorb\\projekty\\hermes-windows-skills'],
    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    close_fds=True
)
```

## Процес моніторингу

Для ловлі моментів, коли PowerShell з'являється:

**`C:\hermes_work\ps_monitor.py`** — фоновий Python скрипт, який кожні 2 секунди перевіряє появу `powershell.exe` або `WindowsTerminal.exe` через WMI. При виявленні логує:
- Час, PID, ім'я процесу
- Батьківський процес (PID + ім'я + команда)

## Після ребуту

Всі зміни в Startup folder і Scheduled Tasks набувають чинності після перезавантаження.

## Proc Watchdog — захист від дублікатів

**`scripts/proc_watchdog.py`** — фоновий монітор, який:
- Стежить за Code.exe кожні 2 секунди
- Якщо main процес без вікна — вбиває (фейковий)
- Якщо >15 процесів — вбиває всі (аномалія)

**`scripts/vs_code_helper.py`** — безпечний запуск:
```python
from vs_code_helper import safe_launch_vscode
safe_launch_vscode('D:\\Sorb\\projekty\\hermes-windows-skills')
```

Правило: GUI програми — тільки через `os.startfile()`. Ніколи через `subprocess.Popen`.
