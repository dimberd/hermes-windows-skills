---
name: windows-diagnostics
description: Проведення діагностики Windows 11 через PowerShell та Sysinternals — пошук зайвих процесів, автозапуску, служб, мережевих з'єднань
---

# Windows Diagnostics

## Як використовувати

### 1. ТОП процесів по пам'яті
```powershell
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 | Format-Table Name, @{N='MB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, Id -AutoSize
```

### 2. Мережеві з'єднання (ESTABLISHED)
```powershell
netstat -ano | Select-String "ESTABLISHED"
```

### 3. Сторонні служби (Auto + Running)
```powershell
Get-CimInstance Win32_Service | Where-Object { 
    $_.StartMode -eq "Auto" -and $_.State -eq "Running" -and 
    $_.PathName -notlike "*system32*" -and $_.PathName -notlike "*syswow64*"
} | Sort-Object Name | Format-Table Name, DisplayName, ProcessId -AutoSize
```

### 4. Автозапуск
```powershell
Get-CimInstance Win32_StartupCommand | Sort-Object Location | Format-Table Name, Command, Location -AutoSize
```

### 5. Сторонні драйвери
```powershell
Get-CimInstance Win32_SystemDriver | Where-Object { 
    $_.State -eq "Running" -and $_.PathName -notlike "*system32*" -and 
    $_.PathName -notlike "*Windows*"
} | Sort-Object Name | Format-Table Name, DisplayName -AutoSize
```

### 6. Sysinternals інструменти
Завантажити окремі утиліти (коли zip не працює):
```bash
curl -kL "https://live.sysinternals.com/autoruns.exe" -o autoruns.exe
curl -kL "https://live.sysinternals.com/procexp.exe" -o procexp.exe
curl -kL "https://live.sysinternals.com/tcpview.exe" -o tcpview.exe
```

### 7. Autorunsc CLI (command-line version)
```bash
# Категорії: l=logon, s=services, t=tasks, b=boot, * = all
autorunsc64.exe -nobanner -accepteula -a l -c -m -s -o autoruns_logon.csv
autorunsc64.exe -nobanner -accepteula -a s -c -m -s -o autoruns_services.csv
autorunsc64.exe -nobanner -accepteula -a t -c -m -s -o autoruns_tasks.csv
```
- `-c` CSV output; `-m` hide Microsoft entries; `-s` verify signatures; `-o <file>` write to file
- `-a "*"` for all categories (use quotes to prevent bash glob expansion)
- CSV is UTF-16 encoded — use `Import-Csv -Encoding Unicode` in PowerShell
- `-nobanner` suppresses the copyright banner

### 8. Memory analysis by process group
```powershell
$groups = Get-Process | Group-Object -Property ProcessName | Sort-Object {($_.Group | Measure-Object WorkingSet64 -Sum).Sum} -Descending
$total = 0
foreach ($g in $groups) {
    $sumMB = [math]::Round(($g.Group | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 1)
    $total += $sumMB
    Write-Host ("{0,-20} x{1,-2} {2,8} MB" -f $g.Name, $g.Count, $sumMB)
}
Write-Host ("TOTAL: {0,8} MB" -f $total)
```

### 9. Знайти батьківський процес (чому процес перезапускається)
```powershell
$p = Get-Process -Name target_process -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "ProcessId = $($p.Id)" | Select-Object ParentProcessId
$pp = Get-Process -Id <ParentProcessId> -ErrorAction SilentlyContinue
Write-Host ("Parent: " + $pp.ProcessName)
```
Якщо процес перезапускається після вбивства — значить його тримає служба або драйвер. Зупиняти треба батька або службу.

### 10. Зупинка зайвих процесів та служб
```powershell
# Зупинити службу і вимкнути
Stop-Service ServiceName -Force
Set-Service ServiceName -StartupType Disabled

# Вбити процес
Stop-Process -Name process_name -Force
taskkill -f -im process_name.exe

# Видалити з автозапуску
Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'AppName' -ErrorAction SilentlyContinue

# Знайти де встановлено програму
(Get-Process -Name app_name).Path
```

## Pitfalls
- PowerShell код треба писати в окремий .ps1 файл і запускати через `powershell -NoProfile -ExecutionPolicy Bypass -File "path.ps1"`, бо bash ламає екранування `$`, `{`, `}`, `` ` ``
- `$pid` — це **readonly змінна** в PowerShell (автоматична), використовувати `$procId` або `$processId` замість `$pid`
- Get-WmiObject Win32_Product дуже повільний, використовувати Get-CimInstance Win32_Service
- Для запуску команд як root в WSL без sudo: `wsl -d Ubuntu-26.04 -u root <команда>`
- Для безпарольного запуску задач в Task Scheduler: `-LogonType S4U` (не вимагає пароля)
