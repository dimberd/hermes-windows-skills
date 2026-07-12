---
name: windows-system-administration
title: Windows 10/11 System Administration & Security
description: Комплексний скіл для системного адміністрування та захисту Windows 10/11 — безпека, моніторинг, управління системою, мережею та користувачами.
tags: [windows, windows-10, windows-11, security, hardening, sysadmin, defender, firewall, bitlocker]
---

# Windows 10/11 System Administration & Security

## Огляд

Скіл для адміністрування та посилення безпеки Windows 10/11. Охоплює політики безпеки, Defender, Firewall, BitLocker, AppLocker, управління користувачами, Event Viewer, мережеві налаштування, оновлення та аудит системи.

---

## 1. Windows Security Hardening (Захист системи)

### 1.1 Microsoft Security Baselines

Microsoft публікує **Security Compliance Toolkit (SCT)** та офіційні **Security Baselines** для Windows 10/11:

```powershell
# Завантажити актуальний Security Compliance Toolkit
# https://learn.microsoft.com/en-us/windows/security/operating-system-security/system-security/windows-security-baseline

# Застосувати політики з baseline
# Використовується LGPO.exe з SCT:
.\LGPO.exe /s C:\Baselines\Windows11-Security-Baseline\GPOs
```

**Ключові області політик безпеки:**
- **User Account Control (UAC)** — завжди на максимальному рівні
- **Windows Defender Antivirus** — ввімкнений, актуальний
- **Firewall** — всі профілі активні, правила за замовчуванням
- **Credential Guard** — апаратна ізоляція облікових даних
- **Device Guard** — білий список дозволених додатків

### 1.2 Windows Defender Antivirus

```powershell
# Статус та стан антивіруса
Get-MpComputerStatus

# Швидке та повне сканування
Start-MpScan -ScanType QuickScan
Start-MpScan -ScanType FullScan

# Автономне сканування (при перезавантаженні)
Start-MpScan -ScanType OfflineScan

# Оновити сигнатури вручну
Update-MpSignature

# Додати винятки (обережно!)
Add-MpPreference -ExclusionPath "C:\Path\To\Exclude"
Add-MpPreference -ExclusionExtension ".exe"
Add-MpPreference -ExclusionProcess "process.exe"

# Контроль надісланих файлів (хмарний захист)
Set-MpPreference -CloudBlockLevel High
Set-MpPreference -CloudTimeout 50
Set-MpPreference -SubmitSamplesConsent Always

# Реальний час
Set-MpPreference -DisableRealtimeMonitoring $false
Set-MpPreference -DisableBehaviorMonitoring $false
```

### 1.3 Windows Defender Firewall

```powershell
# Статус всіх профілів
Get-NetFirewallProfile | Format-Table Name, Enabled

# Список правил
Get-NetFirewallRule | Where { $_.Enabled -eq $true }

# Блокувати вхідні з'єднання (профіль Public)
Set-NetFirewallProfile -Profile Public -DefaultInboundAction Block

# Створити правило: дозволити порт
New-NetFirewallRule -DisplayName "Allow Port 3389" -Direction Inbound -LocalPort 3389 -Protocol TCP -Action Allow

# Логування
Set-NetFirewallProfile -Profile Domain,Private,Public -LogFileName "%SystemRoot%\System32\LogFiles\Firewall\pfirewall.log" -LogMaxSizeKilobytes 16384
```

### 1.4 BitLocker (шифрування диска)

```powershell
# Перевірити статус BitLocker
Get-BitLockerVolume -MountPoint "C:"

# Ввімкнути BitLocker (TPM + PIN)
Enable-BitLocker -MountPoint "C:" -TpmProtector -Pin -RecoveryPasswordProtector

# Зберегти ключі відновлення в AD
Backup-BitLockerKeyProtector -MountPoint "C:" -KeyProtectorId ((Get-BitLockerVolume -MountPoint "C:").KeyProtector[0].KeyProtectorId)

# Вимкнути BitLocker
Disable-BitLocker -MountPoint "C:"

# Статус всіх томів
manage-bde -status
```

### 1.5 AppLocker та SmartScreen

```powershell
# Ввімкнути SmartScreen
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" -Name "SmartScreenEnabled" -Value "RequireAdmin"

# Перевірити політики AppLocker
Get-AppLockerPolicy -Effective | Test-AppLockerPolicy -Path C:\Windows\System32\cmd.exe -User Everyone
```

---

## 2. Управління користувачами та доступом

### 2.1 Local Users and Groups

```powershell
# Список локальних користувачів
Get-LocalUser

# Список груп
Get-LocalGroup

# Створити користувача
$Password = Read-Host -AsSecureString
New-LocalUser -Name "username" -Password $Password -FullName "User Name" -PasswordNeverExpires $false

# Додати до групи (напр. Administrators)
Add-LocalGroupMember -Group "Administrators" -Member "username"

# Видалити користувача
Remove-LocalUser -Name "username"

# Заблокувати / розблокувати користувача
Disable-LocalUser -Name "username"
Enable-LocalUser -Name "username"
```

### 2.2 User Account Control (UAC)

```powershell
# Подивитись рівень UAC
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA"

# Встановити рівень UAC:
# 0 - вимкнено (НЕ РЕКОМЕНДУЄТЬСЯ)
# 1 - повідомляти тільки при змінах
# 2 - завжди повідомляти (рекомендовано)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorAdmin" -Value 2
```

### 2.3 Захист облікових даних

```powershell
# Ввімкнути Credential Guard (потрібна підтримка віртуалізації)
# Через групову політику: Computer Config > Admin Templates > System > Device Guard

# Налаштувати Windows Hello
# Параметри > Облікові записи > Вхід > Windows Hello PIN
```

---

## 3. Мережева безпека

### 3.1 Базові мережеві команди

```cmd
:: Скинути стек TCP/IP
netsh int ip reset
netsh winsock reset

:: Таблиця маршрутизації
route print

:: DNS кеш
ipconfig /flushdns
ipconfig /displaydns

:: ARP кеш
arp -a

:: Активні з'єднання
netstat -ano
netstat -anb
```

### 3.2 Windows Defender Firewall (додатково)

```powershell
# Блокувати вихідний трафік для процесу
New-NetFirewallRule -DisplayName "Block Process Outbound" -Direction Outbound -Program "C:\Path\To\App.exe" -Action Block

# Скинути Firewall до стандарту
netsh advfirewall reset
```

### 3.3 Безпека RDP

```powershell
# Встановити Network Level Authentication (NLA)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 1

# Змінити порт RDP (рекомендовано)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "PortNumber" -Value 3390 -Type DWord
```

---

## 4. Оновлення та моніторинг

### 4.1 Windows Update

```powershell
# Перевірка оновлень (потрібен модуль PSWindowsUpdate)
Install-Module PSWindowsUpdate -Force
Get-WindowsUpdate
Install-WindowsUpdate -AcceptAll -AutoReboot
```

### 4.2 Event Viewer

```powershell
# Події безпеки
Get-WinEvent -LogName Security -MaxEvents 100

# Невдалі спроби входу (Event ID 4625)
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 20

# Системні помилки
Get-WinEvent -LogName System -MaxEvents 50 | Where { $_.LevelDisplayName -eq 'Error' }

# Зберегти логи
wevtutil epl Security C:\Logs\Security.evtx
```

### 4.3 Performance

```powershell
# Пам'ять та диск
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"

# Performance counters
Get-Counter "\Memory\Available MBytes"
Get-Counter "\Processor(_Total)\% Processor Time"
```

---

## 5. Аудит та Compliance

### 5.1 Налаштування аудиту

```powershell
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Account Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Process Creation" /success:enable

# Переглянути поточні політики
auditpol /get /category:*
```

### 5.2 Запущені процеси

```powershell
# Підозрілі процеси
Get-Process | Where { $_.Path -match "\\Temp\\" }

# Мережеві підключення по процесах
Get-NetTCPConnection | Where State -eq "Established" | Group-Object -Property OwningProcess
```

### 5.3 Перевірка цілісності

```powershell
sfc /scannow
DISM /Online /Cleanup-Image /RestoreHealth
chkdsk C: /f /r
```

---

## 6. Реєстр та ключові політики

### Ключові налаштування реєстру

| Політика | Шлях | Дія |
|----------|------|-----|
| LLMNR | HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient | EnableMulticast = 0 |
| NetBIOS | HKLM\SYSTEM\CurrentControlSet\Services\NetBT\Parameters | SMBDeviceEnabled = 0 |
| SMBv1 | HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters | SMB1 = 0 |
| PowerShell v2 | HKLM\SOFTWARE\Microsoft\PowerShell\1 | Disable = 1 |

### Вимкнути непотрібні служби

```powershell
$HighRiskServices = @("RemoteRegistry", "RemoteAccess", "SharedAccess")
foreach ($s in $HighRiskServices) {
    $svc = Get-Service -Name $s -ErrorAction SilentlyContinue
    if ($svc -and $svc.Status -eq 'Running') {
        Stop-Service $svc -Force; Set-Service $svc -StartupType Disabled
    }
}
```

### Політики паролів

```cmd
net accounts /minpwlen:14
net accounts /maxpwage:90
net accounts /minpwage:1
net accounts /lockoutthreshold:5
net accounts /lockoutduration:30
net accounts /lockoutwindow:30
```

---

## 7. Чекліст налаштування безпеки

### Початкове налаштування:
1. **Оновити систему**
2. **Ввімкнути BitLocker**
3. **UAC на максимум**
4. **Defender: хмарний захист, поведінковий моніторинг**
5. **Firewall: всі профілі, вхідні заблоковані**
6. **Вимкнути NetBIOS, LLMNR, SMBv1**
7. **Політики паролів (14+ символів)**
8. **Налаштувати аудит входів**
9. **Tamper Protection ввімкнено**
10. **Auditpol — логування невдалих спроб**

### Швидкий дамп статусу:

```powershell
Get-MpComputerStatus | Select-Object AMRunning, AMProductVersion, RealTimeProtectionEnabled, TamperProtectionSource
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction
Get-BitLockerVolume -ErrorAction SilentlyContinue | Select-Object MountPoint, ProtectionStatus
Get-LocalUser | Where Enabled -eq $true | Select Name, LastLogon
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 10 | Measure-Object
```

---

## 8. Управління живленням для headless/cron роботи

### 🚨 КРИТИЧНЕ РОЗРІЗНЕННЯ: Display vs Sleep

| Режим | Hermes працює? | Пробудження |
|-------|:---:|---|
| **Display OFF** (екран згас) | ✅ **Так** — CPU/RAM працюють, мережа активна | Мишка/клавіша → миттєво |
| **Sleep** (S3 — сон) | ❌ **Ні** — CPU зупинено, мережа відключена | Потрібен Wake Timer або кнопка |
| **Hibernate** (гібернація) | ❌ **Ні** — RAM на диск, живлення вимкнено | Кнопка живлення |

**Display OFF = безпечно для Hermes.** Екран гасне, але комп'ютер продовжує працювати. Це нормальний енергозберігаючий режим.

**Sleep/Hibernate = Hermes перестає відповідати.** CPU зупиняється, мережа зникає, Telegram-бот не доступний. Саме це спричиняє проблему, коли "Hermes перестає відповідати".

### 8.1 Стратегія: комп'ютер працює, але економить енергію

Коли Hermes Agent / cron jobи мають працювати, а користувач не сидить за комп'ютером, потрібен спеціальний план живлення:

| Сценарій | Стратегія |
|----------|-----------|
| **На зарядці** | Ніколи не спати, ніколи не гібернувати. Cron працює 24/7. Екран може гаснути для економії |
| **На батареї** | Спати після 15-30 хв бездіяльності, але Wake Timers увімкнені |
| **Wake Timers** | **Критично важливо** — мають бути включені для обох режимів |

### 8.2 Створення кастомного плану живлення

> ⚠️ **ML/GPU workloads note:** The power plan below sets CPU Max to 80% and USB Selective Suspend ON — these THROTTLE ONNX/ML inference (Rope, ComfyUI, whisper, local LLMs). See `references/power-optimization-ml-workloads.md` for ML-specific overrides (USB suspend OFF, CPU 100%). Apply those AFTER creating the base plan.
> 
See `references/power-plan-hermes-agent.md` (oszczedny — power-saving) and `references/power-plan-hermes-server.md` (Serwer — 24/7 no sleep) for exact re-create steps.
> 🖥️ **Server mode ("Hermes Agent - Serwer"):** For the "monitors off after 10 min, computer never sleeps" pattern, see `references/power-plan-hermes-server.md`. That plan keeps CPU at 100% on AC and disables USB suspend so mouse/keyboard always wake the display.

```powershell
# 1. Склонувати існуючий план "Енергозбереження"
powercfg -DUPLICATESCHEME a1841308-3541-4fab-bc81-f71556f20b4a
# GUID виведеться після команди, запам'ятати

# 2. Перейменувати
powercfg -CHANGENAME <GUID> "Hermes Agent - oszczedny"

# 3. Активувати
powercfg -SETACTIVE <GUID>

# 4. Базові налаштування
powercfg -CHANGE -monitor-timeout-ac 3
powercfg -CHANGE -monitor-timeout-dc 2
powercfg -CHANGE -disk-timeout-ac 5
powercfg -CHANGE -disk-timeout-dc 3
powercfg -CHANGE -standby-timeout-ac 0     # НЕ спати на зарядці
powercfg -CHANGE -standby-timeout-dc 30
powercfg -CHANGE -hibernate-timeout-ac 0
powercfg -CHANGE -hibernate-timeout-dc 60

# 5. CPU — енергозбереження
powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN 5
powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN 5
powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 80
powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 50

# 6. Wake Timers — ОБОВ'ЯЗКОВО
powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1
powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1

# 7. PCI Express ASPM
powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_PCIEXPRESS ASPM 2
powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_PCIEXPRESS ASPM 2

# 8. USB selective suspend
powercfg -SETACVALUEINDEX SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1
powercfg -SETDCVALUEINDEX SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1

# 9. WiFi — середнє/макс енергозбереження
powercfg -SETACVALUEINDEX SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 12bbebe6-58d6-4636-95bb-3217ef867c1a 2
powercfg -SETDCVALUEINDEX SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 12bbebe6-58d6-4636-95bb-3217ef867c1a 3

# 10. Hybrid sleep — вимкнути
powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0
powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0

# 11. Яскравість на батареї
powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_VIDEO VIDEONORMALLEVEL 30
```

### 8.3 Перевірка

```powershell
powercfg -GETACTIVESCHEME
powercfg -Q
powercfg -LIST
```

### 8.4 Важливі зауваження

- **Sleep** (S3) ≠ робота. CPU зупиняється — жодні cron/скрипти не працюють
- **Hibernate** = повне вимкнення. Вміст RAM на диск, живлення відсутнє
- **Display OFF** = Hermes працює далі. Екран просто гасне, пробуджується мишкою/клавішею
- **Wake Timers** дозволяють cron розбудити комп'ютер зі Sleep, виконати роботу і знову заснути
- **Disk idle**: якщо диск вимикається, а cron пише логи — диск прокинеться автоматично

### 8.5 План "Hermes Agent - Serwer" (серверний режим)

Підходить коли: Hermes має працювати 24/7, але екран може гаснути для економії.

**Відмінність від "oszczedny":**
- Екран гасне через 10 хв (а не 3 хв) — щоб не заважати, коли користувач працює
- Сон/гібернація — НІКОЛИ (в oszczedny були таймаути на батареї)
- USB selective suspend — ВИМКНЕНО (щоб мишка/клавіатура точно будили монітор)
- CPU Max на мережі — 100% (серверна продуктивність)

```powershell
# === ШВИДКЕ НАЛАШТУВАННЯ (простий спосіб) ===

# 1. Встановити базові параметри
powercfg -CHANGE -monitor-timeout-ac 10   # 10 хв
powercfg -CHANGE -monitor-timeout-dc 10   # 10 хв на батареї
powercfg -CHANGE -standby-timeout-ac 0    # НІКОЛИ не спати
powercfg -CHANGE -standby-timeout-dc 0    # НІКОЛИ не спати
powercfg -CHANGE -hibernate-timeout-ac 0  # НІКОЛИ
powercfg -CHANGE -hibernate-timeout-dc 0  # НІКОЛИ
powercfg -CHANGE -disk-timeout-ac 0       # НІКОЛИ не вимикати диск
powercfg -CHANGE -disk-timeout-dc 0

# === РОЗШИРЕНЕ НАЛАШТУВАННЯ (через новий план з High Performance) ===

$highPerfGuid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"

# 1. Склонувати High Performance
$result = powercfg -DUPLICATESCHEME $highPerfGuid
# GUID з'явиться у виводі, запам'ятати
$GUID = "СКОПІЙОВАНИЙ_GUID"

# 2. Перейменувати
powercfg -CHANGENAME $GUID "Hermes Agent - Serwer" "Nigdy nie śpi - 24/7 Hermes"

# 3. Базові налаштування
powercfg -CHANGE -monitor-timeout-ac 10
powercfg -CHANGE -monitor-timeout-dc 10
powercfg -CHANGE -standby-timeout-ac 0    # НЕ спати!
powercfg -CHANGE -standby-timeout-dc 0
powercfg -CHANGE -hibernate-timeout-ac 0
powercfg -CHANGE -hibernate-timeout-dc 0
powercfg -CHANGE -disk-timeout-ac 0
powercfg -CHANGE -disk-timeout-dc 0

# 4. CPU — 100% на мережі для сервера
powercfg -SETACVALUEINDEX $GUID SUB_PROCESSOR PROCTHROTTLEMAX 100
powercfg -SETDCVALUEINDEX $GUID SUB_PROCESSOR PROCTHROTTLEMAX 80

# 5. Wake Timers — увімкнено (для cron)
powercfg -SETACVALUEINDEX $GUID SUB_SLEEP RTCWAKE 1
powercfg -SETDCVALUEINDEX $GUID SUB_SLEEP RTCWAKE 1

# 6. USB selective suspend — ВИМКНЕНО (щоб мишка будила монітор)
powercfg -SETACVALUEINDEX $GUID "2a737441-1930-4402-8d77-b2bebba308a3" "48e6b7a6-50f5-4782-a5d4-53bb8f07e226" 0
powercfg -SETDCVALUEINDEX $GUID "2a737441-1930-4402-8d77-b2bebba308a3" "48e6b7a6-50f5-4782-a5d4-53bb8f07e226" 0

# 7. Активувати
powercfg -SETACTIVE $GUID

# 8. Вимкнути hiberfil.sys (економія ~75% RAM на диску)
powercfg -H OFF

# Перевірка
powercfg -GETACTIVESCHEME
powercfg -Q
```

**Параметри плану "Hermes Agent - Serwer":**

| Параметр | Мережа (AC) | Батарея (DC) |
|---|---|---|
| Екран | 10 хв | 10 хв |
| Сон | НІКОЛИ | НІКОЛИ |
| Гібернація | НІКОЛИ | НІКОЛИ |
| Диск | НІКОЛИ | НІКОЛИ |
| CPU | 5–100% | 5–80% |
| Wake timers | Увімкнено | Увімкнено |
| USB suspend | ВИМКНЕНО | ВИМКНЕНО |
| Hiberfil.sys | ВИМКНЕНО | — |

### 8.6 Як повернути стандартний план

```powershell
# Список всіх планів
powercfg -LIST

# Активувати збалансований
powercfg -SETACTIVE SCHEME_BALANCED

# Активувати високопродуктивний
powercfg -SETACTIVE SCHEME_MIN
```

---

## 9. Task Scheduler — автозапуск без логіну (S4U) та SYSTEM elevation

### S4U (Service for User) — без пароля для періодичних задач

Див. нижче S4U recipe для PowerShell `Register-ScheduledTask`.

### SYSTEM elevation патерн — для MSI та адмін-операцій

`references/schtasks-elevation-pattern.md` — коли потрібно виконати команду з **SYSTEM привілеями без UAC** (встановлення/видалення MSI, bcdedit, HKLM registry):

```bash
# Створюємо разову задачу з SYSTEM (найвищі права)
schtasks /create /tn "TaskName" /sc once /st 00:00 /rl highest /ru SYSTEM /tr "msiexec /x {GUID} /quiet /norestart" /f
schtasks /run /tn "TaskName"
sleep 10
schtasks /delete /tn "TaskName" /f
```

Ключова відмінність від S4U: `/ru SYSTEM` (а не `-LogonType S4U -UserId 'user'`), `/rl highest`. Працює з `cmd.exe` напряму (не потребує PowerShell).

### Коли потрібно

Сервіси, які мають стартувати при включенні комп'ютера **до того, як користував залогінився**:
- Gateway / Telegram бот
- Hindsight API в WSL
- Watchdog скрипти
- Будь-які фонові сервіси (cron, моніторинг)

### Проблема: пароль

PowerShell `Register-ScheduledTask` з `-LogonType Password` вимагає пароль користувача, який неможливо передати з git-bash/автоматично. Рішення — **S4U logon type**.

### ✅ S4U (Service for User) — без пароля

```powershell
$action = New-ScheduledTaskAction -Execute 'C:\Windows\System32\wsl.exe' -Argument '-d Ubuntu-26.04 -u user -- /path/to/script.sh'
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -Compatibility Win8 -ExecutionTimeLimit 0
$principal = New-ScheduledTaskPrincipal -UserId 'USERNAME' -LogonType S4U -RunLevel Highest
Register-ScheduledTask -TaskName 'TaskName' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
```

**Ключові параметри:**
| Параметр | Значення | Чому |
|---|---|---|
| `-LogonType S4U` | S4U | Не потребує пароля (на відміну від `Password`) |
| `-Compatibility Win8` | Win8 | Сумісність з S4U на Windows 10/11 |
| `-MultipleInstances IgnoreNew` | IgnoreNew | Не створює дублікатів при повторному запуску |
| `-ExecutionTimeLimit 0` | 0 | Безлімітний час виконання (для сервісів/демонів) |
| `-RestartCount 3` | 3 | Авто-перезапуск при збої (до 3 разів) |

### Дублікати процесів (важливо!)

Якщо задача запускає процес, який може накопичувати копії (наприклад, `hindsight-api` створює новий процес при кожному запуску), **обов'язково** додати health-check в обгортку:

```bash
#!/bin/bash
# start_script.sh — wrapper з захистом від дублікатів
PORT=8888
if curl -s --connect-timeout 3 http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "Process вже працює. Виходжу."
    exit 0
fi
# Запуск
/path/to/your-service &
```

### Комбінація: система стартує до логіну

Для повного автозапуску без логіну створюються 2-3 задачі з S4U:

```powershell
# 1. Gateway (старт системи)
$principal = New-ScheduledTaskPrincipal -UserId 'PL_home' -LogonType S4U -RunLevel Highest
Register-ScheduledTask ... -Trigger (New-ScheduledTaskTrigger -AtStartup) ...

# 2. WSL сервіс (старт системи)
Register-ScheduledTask ... -Trigger (New-ScheduledTaskTrigger -AtStartup) ...

# 3. Watchdog (старт системи + логін для резерву)
Register-ScheduledTask ... -Trigger @(New-ScheduledTaskTrigger -AtStartup, New-ScheduledTaskTrigger -AtLogOn) ...
```

### Перевірка

```powershell
schtasks /Query /FO LIST /V | Select-String -Pattern 'TaskName|Status|Schedule Type|Run As|Logon Mode|Task To Run' -Context 0,0
```

### Типові помилки

| Помилка | Причина | Рішення |
|---------|---------|---------|
| `Назва користувача або пароль неправильні` | Спроба `-LogonType Password` без пароля | Замінити на `-LogonType S4U` |
| Задача не стартує при рестарті | Тригер `AtLogon` вимагає логіну | Використати `AtStartup` |
| Процес є, а health endpoint не відповідає | WLS не стартував до кінця | Додати `sleep` або `RestartCount` в task settings |
| Дублікати процесів при кожному `schtasks /Run` | Відсутній health-check в wrapper | Додати curl перевірку перед запуском |

## 10. Windows Lock Screen & Personalization Management

### Lock Screen vs Desktop Wallpaper — critical distinction

| Element | What it is | How to change |
|---------|-----------|---------------|
| **Desktop wallpaper** (фон) | The image behind your desktop icons | `SystemParametersInfo(0x0014, ...)` or Settings → Personalization → Background |
| **Lock screen** (екран блокування/блокади) | The screen shown before login (Win+L) | GPO policy (HKLM) or Settings → Personalization → Lock Screen |

**Common mistake:** Changing desktop wallpaper does NOT affect the lock screen. They are completely separate settings in Windows.

### 10.1 Set lock screen to a solid color (e.g., black)

When you need a minimal/no-image lock screen:

```powershell
# 1. Create a solid black PNG
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap 1920, 1080
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.Clear([System.Drawing.Color]::FromArgb(0, 0, 0))
$gfx.Dispose()
$final = "$env:LOCALAPPDATA\Microsoft\Windows\Themes\black_lock_screen.png"
$bmp.Save($final, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

# 2. Set via GPO registry (requires admin)
$policyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization'
if (-not (Test-Path $policyPath)) {
    New-Item -Path $policyPath -Force | Out-Null
}
Set-ItemProperty -Path $policyPath -Name 'LockScreenImage' -Value $final -Type String -Force

# 3. Disable Windows Spotlight (prevents overriding)
$spotPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'
Set-ItemProperty -Path $spotPath -Name 'SystemPaneSuggestionsEnabled' -Value 0 -Type DWord -Force

# 4. Apply
gpupdate /force
```

**To restore Windows Spotlight later:**
```powershell
Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization' -Name 'LockScreenImage' -Force
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager' -Name 'SystemPaneSuggestionsEnabled' -Value 1 -Type DWord -Force
gpupdate /force
```

### 10.2 Set desktop wallpaper programmatically

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WallpaperAPI {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
}
"@

# SPIF_UPDATEINIFILE (0x01) | SPIF_SENDCHANGE (0x02)
[WallpaperAPI]::SystemParametersInfo(0x0014, 0, "C:\path\to\image.jpg", 3)
```

### 10.3 Current lock screen status (diagnostics)

```powershell
# Check custom lock screen image (GPO)
$policyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization'
if (Test-Path $policyPath) {
    $val = (Get-ItemProperty -Path $policyPath -Name LockScreenImage -ErrorAction SilentlyContinue).LockScreenImage
    Write-Host "Custom lock screen image: $val"
}

# Spotlight status
$spotPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'
$spotlight = (Get-ItemProperty -Path $spotPath -Name SystemPaneSuggestionsEnabled -ErrorAction SilentlyContinue).SystemPaneSuggestionsEnabled
if ($spotlight -eq 1) { Write-Host "Spotlight: ENABLED" } else { Write-Host "Spotlight: DISABLED" }

# Current wallpaper
$wallpaper = (Get-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name Wallpaper).Wallpaper
Write-Host "Desktop wallpaper: $wallpaper"

# Active theme file
$theme = (Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes' -Name CurrentTheme).CurrentTheme
Write-Host "Active theme: $theme"
```

### 10.4 WinRT LockScreen API reliability (pitfall)

The `[Windows.System.UserProfile.LockScreen]::SetImageFileAsync()` API in PowerShell 5.1 frequently fails with `System.__ComObject` errors — the WinRT interop layer is unreliable from PowerShell when called via git-bash. Symptoms:

- `GetFileFromPathAsync` returns `System.__ComObject` instead of `StorageFile`
- `AsTask()` fails with "Unable to find type" errors
- The lock screen silently stays unchanged despite no errors

**Reliable alternatives:**
- **GPO method** (requires admin): Set `HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization\LockScreenImage` to the image path, run `gpupdate /force`.
- **Manual:** Have the user set it via Settings → Personalization → Lock Screen.
- **Desktop wallpaper** (easier): `SystemParametersInfo(0x0014, ...)` always works via `user32.dll`.

### 10.5 Modify theme file (.theme)

The `.theme` file is an INI-format file. Key sections:

```ini
[Control Panel\Desktop]
Wallpaper=C:\path\to\wallpaper.jpg
PicturePosition=4                ; 0=Center, 1=Tile, 2=Stretch, 3=Fit, 4=Fill, 5=Span
Wallpaper1=...                   ; Multi-monitor wallpaper
WallpaperWriteTime=134272565320000000

[VisualStyles]
Path=%SystemRoot%\resources\themes\Aero\Aero.msstyles
SystemMode=Dark                  ; Dark mode toggle
AppMode=Dark
```

To change wallpaper via theme file:
1. Edit the `Custom.theme` file at `%LOCALAPPDATA%\Microsoft\Windows\Themes\Custom.theme`
2. Update the `Wallpaper=` path
3. Remove `Wallpaper1=` and `Wallpaper2=` entries if switching from multi-monitor to single
4. Apply by running: `gpupdate /force` and then calling `SystemParametersInfo`

### Pitfalls

1. **HKLM GPO requires admin** — `HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization` needs elevation. Without it, the policy silently fails.
2. **Lock screen ≠ desktop wallpaper** — Changing one does NOT affect the other. Always clarify which the user means.
3. **Windows Spotlight overrides custom lock screen** — If Spotlight is enabled, the custom lock screen image won't show. Must disable Spotlight first.
4. **Theme file Wallpaper1/Wallpaper2** — These are for multi-monitor setups. If you set only the main `Wallpaper=` but leave old `Wallpaper1=` entries, Windows may still use the old images.
5. **gpupdate required** — Setting the HKLM policy is not enough; `gpupdate /force` must run for it to take effect immediately.
6. **Python ctypes preferred over PowerShell** — Use `scripts/wallpaper.py` (this skill) for wallpaper/lock screen changes. It calls Windows API directly in-process with `ctypes` — zero processes, zero windows. Avoid using `powershell.exe` for these operations as it opens visible windows even with `-WindowStyle Hidden`.

---

## VHD/VHDX Management

`references/vhd-management.md` — діагностика VHD дисків, перевірка auto-mount (реєстр `MountedDevices`), гарантоване монтування через Scheduled Task (S4U), створення/відмонтування VHDX, типові проблеми.

## Stuck/Freeze Windows Troubleshooting

Коли вікно програми зависає (не можна закрити, згорнути, розгорнути, не працюють клавіші):

```powershell
# 1. Спробувати закрити через Task Manager
taskkill /IM pwsh.exe /F

# 2. Якщо не закривається — знайти батьківський процес
Get-Process pwsh | Select-Object Id, Parent, StartTime

# 3. Зупинити через WMI (сильніше ніж taskkill)
Get-WmiObject Win32_Process -Filter "Name='pwsh.exe'" | ForEach-Object { $_.Terminate() }

# 4. Якщо не допомагає — перезапустити Windows Explorer (вбиває всі stuck вікна)
Stop-Process -Name explorer -Force
# Explorer сам рестартне через кілька секунд

# 5. Аварійний вихід — створити нову сесію (logoff)
logoff
```

**Якщо пропали функціональні клавіші (F1-F12):**
```powershell
# Перевірити чи F Lock активовано (на клавіатурах з Fn Lock)
# Або: налаштувати Windows Terminal → Settings → Actions → Keyboard Shortcuts

# Скинути налаштування PowerShell profile
Remove-Item $PROFILE -Force -ErrorAction SilentlyContinue
```

### 10.1 Завантаження інструментів

Sysinternals Suite — 60+ утиліт для діагностики Windows. Найважливіші:

| Утиліта | Призначення | Посилання |
|---------|-------------|-----------|
| **Autoruns** | Аналіз автозапуску (startup, services, drivers, scheduled tasks) | `live.sysinternals.com/autoruns.exe` |
| **Process Explorer** | Детальний перегляд процесів (деревоподібний, PID, батьки, DLL) | `live.sysinternals.com/procexp.exe` |
| **TCPView** | Активні мережеві з'єднання по процесах | `live.sysinternals.com/tcpview.exe` |

**Завантаження:**
```bash
curl -kL "https://live.sysinternals.com/autoruns.exe" -o autoruns.exe
curl -kL "https://live.sysinternals.com/procexp.exe" -o procexp.exe
curl -kL "https://live.sysinternals.com/tcpview.exe" -o tcpview.exe
```

### 10.2 Вбудована діагностика (без Sysinternals)

Для CLI/автоматизованої діагностики зручніше використовувати вбудовані PowerShell команди, оскільки Sysinternals GUI не працюють з terminal tool:

**Мережеві з'єднання:**
```powershell
netstat -ano | Select-String "ESTABLISHED"
```

**Список сторонніх служб (Auto+Running):**
```powershell
Get-CimInstance Win32_Service | Where-Object { 
    $_.StartMode -eq "Auto" -and $_.State -eq "Running" -and 
    $_.PathName -notlike "*system32*" 
} | Sort-Object Name | Format-Table Name, DisplayName, ProcessId
```

**Автозапуск:**
```powershell
Get-CimInstance Win32_StartupCommand | Sort-Object Location | Format-Table Name, Command, Location
```

**Топ процесів по пам'яті:**
```powershell
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 | 
    Format-Table Name, @{N="MB";E={[math]::Round($_.WorkingSet64/1MB,1)}}, Id
```

**Сторонні драйвери:**
```powershell
Get-CimInstance Win32_SystemDriver | Where-Object { 
    $_.State -eq "Running" -and $_.PathName -notlike "*system32*" -and 
    $_.PathName -notlike "*Windows*"
} | Sort-Object Name | Format-Table Name, DisplayName
```

### 10.3 Процес очищення пам'яті

Коли знайдено процес, що жере пам'ять:

1. Ідентифікувати — чи потрібен він взагалі (Google, Kite AI, NetCut, Razer тощо)
2. Зупинити — `Stop-Process -Name <name> -Force`
3. Перевірити чи рестарнув — якщо рестарнув, значить це служба або автостарт
4. Якщо служба — вимкнути:
   ```powershell
   Stop-Service <Name> -Force
   Set-Service <Name> -StartupType Disabled
   ```
5. Якщо автозапуск — видалити з реєстру:
   ```powershell
   Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name '<Name>' -EA 0
   ```
6. Знайти батьківський процес (якщо рестарнує):
   ```powershell
   $p = Get-Process <name> -EA 0
   $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $($p.Id)" | Select-Object ParentProcessId
   Get-Process -Id $parent.ParentProcessId
   ```

## 11. Troubleshooting — PowerShell display issues & .NET runtime

`references/powershell-display-issues.md` — діагностика та виправлення:
- Пропалі кнопки вікна (Windows Terminal focus mode `maximizedFocus`, conhost vs Windows Terminal)
- pwsh не стартує — `System.Private.CoreLib.dll` not found (DOTNET_ROOT, .NET runtime version mismatch)
- PSReadLine VT processing errors (profile fix)
- Повна перевірка конфігурації: DPI, Windows Terminal settings, console host, профіль

`references/powershell-clean-reinstall.md` — повна процедура чистого перевстановлення PowerShell 7:
- Видалення через schtasks SYSTEM (без UAC), очищення старих конфігів, встановлення з MSI
- Створення чистого профілю, перевірка працездатності

`references/schtasks-elevation-pattern.md` — загальний патерн запуску msiexec/bcdedit/HKLM операцій з SYSTEM привілеями:
- Коли `Start-Process -Verb RunAs` не підходить (UAC popup)
- Як `schtasks /ru SYSTEM /rl highest` вирішує проблему
- Порівняння з VBS silent_run та subprocess.Popen

### Консольне кодування

На Windows з польською локаллю `Console.OutputEncoding` = **ibm852** (OEM Central European). Це може спричиняти проблеми з виводом Unicode (кирилиця, спецсимволи):

```powershell
# Перевірити поточне кодування
[Console]::OutputEncoding

# Змінити на UTF-8 (в профілі)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

.NET System.Text.Encoding::Default зазвичай `utf-8`, але консоль використовує ibm852 через Windows код-пейдж регіону.

### PSReadLine 2.4.5 — особливості

| Параметр | Тип | Правильний синтаксис |
|----------|-----|---------------------|
| `-HistoryNoDuplicates` | Switch | `Set-PSReadLineOption -HistoryNoDuplicates` (без `$true`!) |
| `-PredictionSource` | Enum | `History`, `HistoryAndPlugin`, `Plugin`, `Azure`, `None` |
| `-BellStyle` | Enum | `Audible`, `Visual`, `None` |

В PSReadLine 2.4.5 `HistoryNoDuplicates` — switch-параметр, не приймає значення. `-HistoryNoDuplicates $true` викине помилку `A positional parameter cannot be found that accepts argument 'True'`.

### powershell.config.json

`C:\Program Files\PowerShell\7\powershell.config.json` встановлює системну політику виконання:
```json
{
  "Microsoft.PowerShell:ExecutionPolicy": "RemoteSigned",
  "WindowsPowerShellCompatibilityModuleDenyList": ["PSScheduledJob", "BestPractices", "UpdateServices"]
}
```

Це безпечніше ніж `Unrestricted` (який був у старій інсталяції). Змінити:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope LocalMachine
```

### HKCU\Console — глобальні налаштування консолі

Реєстр `HKCU\Console` впливає на ВСІ консольні вікна (cmd, powershell, pwsh без Windows Terminal):

| Параметр | Типове значення | Опис |
|----------|----------------|------|
| `ForceV2` | 1 | Сучасний console renderer (Win10+) — має всі кнопки вікна |
| `QuickEdit` | 1 | Виділення мишкою без додаткового меню |
| `CursorSize` | 25 | Розмір курсора в процентах |
| `ColorTable00-15` | Кастомні | 16 кольорів палітри |
| `HistoryBufferSize` | 50 | Розмір буфера історії |
| `ScreenBufferSize` | 0x23290078 | Розмір буфера екрану |
| `WindowSize` | 0x1e0078 | Розмір вікна в символах |

Ці налаштування НЕ впливають на Windows Terminal — він має власний профіль.

## 12. Troubleshooting — PowerShell з git-bash (Hermes/Windows)

### 🚨 RULE: PowerShell windows MUST NOT flash on user's desktop

Calling `powershell.exe` directly from bash opens a visible PowerShell window that flashes on screen — extremely disruptive to the user.

**Known sources of PowerShell windows on this system (2026-07-12):**

| Джерело | Причина | Статус |
|---------|---------|--------|
| `computer-use-mcp` (Node.js MCP) | `execFileAsync('powershell.exe', ..., {windowsHide: true})` для `focus_window` | ⚠️ `windowsHide: true` може не спрацювати на деяких Windows |
| `HermesPostBoot` (Scheduled Task) | Запускав .ps1 напряму | ✅ Виправлено: wscript.exe + VBS |
| `Hermes Watchdog v2` (Scheduled Task) | Без `-WindowStyle Hidden` | ✅ Виправлено: додано Hidden |
| `hermes_startup.ps1` (Startup folder) | Windows запускав .ps1 у видимому вікні | ✅ Виправлено: .vbs + WshShell.Run style 0 |

**Для моніторингу нових запусків PowerShell:** `scripts/ps_monitor.py` (в цьому скілі) — фоновий Python WMI монітор. Запуск: `python scripts/ps_monitor.py`.

**Див. також:** 
- проект `hermes-windows-skills`, `docs/references/powershell-window-suppression.md`
- `references/backup-procedure.md` — backup z wersjonowaniem ZIP na D:\Sorb\backup\

### 🐍 Proc Watchdog — zombie detection для ВСІХ GUI apps (20+ додатків)

Скрипт `scripts/proc_watchdog.py` (фоновий, 2s інтервал) перевіряє: Code.exe, chrome.exe, firefox.exe, brave.exe, WINWORD.EXE, EXCEL.EXE, Telegram.exe, Discord.exe, Spotify.exe та інші. Детекція zombie: перевірка `MainWindowHandle` для кожного PID. Якщо жоден процес не має вікна → всі zombie → `taskkill /F /IM`. Лог у `proc_watchdog.log`. Запуск: `python scripts/proc_watchdog.py` (через CREATE_NO_WINDOW + DETACHED_PROCESS).

**Скрипти в цьому скілі (Hermes ecosystem diagnostics & maintenance):**\n\n| Скрипт | Функція | Запуск |\n|--------|---------|--------|\n| `scripts/hermes_diag.py` | Комплексна діагностика: Gateway, MCP, zombie, WSL, RAM | `python scripts/hermes_diag.py check` |\n| `scripts/proc_watchdog.py` | Фоновий монітор (2s) — Code.exe, Chrome, Firefox, Word, Excel, Telegram + zombie kill | `python scripts/proc_watchdog.py` |\n| `scripts/ps_monitor.py` | Монітор запуску powershell.exe / WindowsTerminal.exe | `python scripts/ps_monitor.py` |\n| `scripts/pre_update_backup.py` | Backup config.yaml + skills + pip list | `python scripts/pre_update_backup.py` |\n| `scripts/hermes_update_check.py` | Staged update: download→compare 33 config sections (3 generations)→risk analysis→apply/block | `python scripts/hermes_update_check.py` |\n| `scripts/wallpaper.py` | Wallpaper + lock screen via ctypes (zero windows) | `python scripts/wallpaper.py` |\n| `scripts/vs_code_helper.py` | Safe VS Code launch — checks duplicates, kills zombies first | `python scripts/vs_code_helper.py` |
**Див. також:** 
- проект `hermes-windows-skills`, `docs/references/powershell-window-suppression.md`
- `references/backup-procedure.md` — backup z wersjonowaniem ZIP na D:\Sorb\backup\

### 🐍 Proc Watchdog — запобігання дублікатам процесів

**Файли:**
- `C:\\hermes_work\\proc_watchdog.py` — фоновий монітор, стежить за Code.exe, Chrome, Word, Excel, Telegram та іншими GUI апп. Кожні 2с перевіряє чи мають вікно. Якщо жоден не має → zombie → вбиває.
- `C:\\hermes_work\\vs_code_helper.py` — безпечний запуск VS Code з перевіркою дублікатів
- `C:\\hermes_work\\hermes_diag.py` — сценарій дій при проблемах: перевіряє Gateway, MCP, zombie, WSL, RAM. Запуск: `python hermes_diag.py check/fix/report`

### 🔐 Оновлення Hermes — безпечна процедура

**Файли:**
- `C:\\hermes_work\\hermes_update_safe.py` — безпечний update: backup → порівняння 33 секцій config → рапорт → децизія → update
- `C:\\hermes_work\\hermes_update_check.py` — нічний cron (1:00) для перевірки оновлень
- `C:\\hermes_work\\pre_update_backup.py` — бекап config.yaml + скіли + пакети

**Правила:**

1. **Перед кожним апдейтом** (авто чи ручним): `python hermes_update_safe.py`
2. **Порівнюються 3 генерації:** backup → obecny → nowy (33 секції config)
3. **Якщо змінені критичні секції** (mcp_servers, display, terminal, memory, tts, stt, platform_toolsets) → блокуємо апдейт
4. **Після апдейту** треба перевірити: Gateway, MCP, zombie
5. **Якщо user каже `hermes update` вручну** — теж спочатку порівняти, потім звіт, потім децизія

**Хроніми ключі config (не можна надписувати):**
- mcp_servers, display, terminal, memory, tts, stt, image_gen, code_execution, session_reset, platform_toolsets, plugins, model, approvals

**Див. також:** `references/backup-versioning-3-2-1.md` — backup z wersjonowaniem ZIP, reguła 3-2-1, GitHub offsite, recovery instrukcja.

### 🧟 Zombie detection

Nie tylko VS Code! Wszystkie GUI aplikacje:
- Code.exe, chrome.exe, firefox.exe, WINWORD.EXE, EXCEL.EXE, Telegram.exe, Discord.exe, Spotify.exe...
- Proc watchdog sprawdza KAŻDY proces czy ma MainWindowHandle
- Jeśli proces istnieje ale nie ma okna → zombie → zabija wszystkie instancje

### 📋 Szenariusz system recovery (pełny)

`python K:\\hermes_work\\hermes_diag.py check` — sprawdza wszystko
`python K:\\hermes_work\\hermes_diag.py fix` — naprawia co się da

| Problem | Detection | Fix |
|---------|-----------|-----|
| Gateway down | `wmic pythonw.exe %gateway%` | `schtasks /Run Hermes_Gateway` |
| MCP 1024×768 | `computer_toggle_session` shows fallback | Restart komputera |
| Zombie procesy | `check_zombies()` 20+ GUI apps | `taskkill /F /IM` |
| WSL nie działa | `wsl -l -v` | `wsl -d Ubuntu-26.04` |
| Wysokie RAM >85% | `wmic OS get FreePhysicalMemory` | Alarm

**❌ WRONG (flashes window):**
```bash
powershell.exe -NoProfile -Command "Write-Host 'test'"
```

**✅ BEST (Python ctypes — no external process, zero windows):**
Python with `ctypes` calls Windows API directly in-process — no new process, no window:
```python
import ctypes
ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, r"C:\path\to\image.jpg", 3)
```
This is the most reliable approach. See `scripts/wallpaper.py` (in this skill's directory) for `set_desktop_wallpaper()` and `set_lock_screen_gpo()`.

**✅ ALSO GOOD (VBS wrapper — hidden PowerShell process):**
```vbs
' silent_run.vbs — launches PowerShell completely invisibly
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & _
  WScript.Arguments(0) & """", 0, False
```

Execution:
```bash
cscript.exe //Nologo "C:\path\to\silent_run.vbs" "C:\path\to\script.ps1"
```

**Template file:** `templates/silent_run.vbs` (in this skill's directory). Reusable across projects.
**Script:** `scripts/wallpaper.py` — Python ctypes-based wallpaper/lock screen (preferred over PowerShell).

Keep `silent_run.vbs` in a stable location (e.g., `$env:TEMP` or `C:\Scripts\`) for reuse.

Під час запуску PowerShell через `terminal` (git-bash/MSYS2) є **важливі обмеження**:

### 10.1 `$_` ламається git-bash

```powershell
# ❌ НЕ ПРАЦЮЄ з git-bash — $_ сприймається як шлях (MSYS підстановка)
Get-LocalUser | Where-Object { $_.Enabled -eq $true }

# ✅ ПРАЦЮЄ — використовуйте -NoProfile та обгортайте в простий запит
powershell.exe -NoProfile -Command "Get-LocalUser | Where-Object { `$_.Enabled -eq `$true }"
```
Або найпростіше — виносити складні команди в `.ps1` файл і виконувати його:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\path\to\script.ps1"
```

### 10.2 `$null` з `2>` також не працює

```powershell
# ❌ НЕ ПРАЦЮЄ:
Get-CimInstance Win32_Product | Where-Object { $_.Name -like '*ESET*' } 2>$null

# ✅ ПРАЦЮЄ — просто опустіть перенаправлення $null
Get-CimInstance Win32_Product | Where-Object { $_.Name -like '*ESET*' }
```

### 10.3 `Get-CimInstance Win32_Product` — дуже повільний

`Get-CimInstance Win32_Product` може висіти **30+ секунд**, бо тригерує перевірку інсталятора Windows (MSI). По можливості замінюйте на:
- `Get-ItemProperty HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*` — швидкий список встановлених програм
- `Get-CimInstance AntiVirusProduct -Namespace root/SecurityCenter2` — тільки антивіруси

### 10.4 `Get-LocalUser` з фільтрацією

Проблема: git-bash сприймає `$_.Enabled` як `/c/Users/PL_home.Enabled`. Рішення: читайте всіх і фільтруйте через `Select-Object`:
```powershell
Get-LocalUser | Select-Object Name, Enabled, LastLogon, PasswordExpires
```

### 10.5 Security Center кеш

Після видалення антивіруса (ESET тощо) запис у `Get-CimInstance AntiVirusProduct -Namespace root/SecurityCenter2` може залишатися до **перезавантаження**. Файли та реєстр вже очищені — кеш оновиться після reboot.

---

## 12. Python venv conflicts with Hermes on Windows

### Problem

Hermes from git-bash sets `PYTHONPATH` to its own venv (Python 3.14). This breaks external Python projects (Rope, ComfyUI, etc.) that use their own venv with a different Python version. Symptoms: `ModuleNotFoundError` for numpy C-extensions, wrong Python version detection.

### Reference

`skill_view(name="windows-system-administration", file_path="references/python-venv-conflicts.md")`

### Quick fix

In a `.bat` launcher:
```bat
@echo off
set PYTHONPATH=
call venv\Scripts\activate.bat
python app.py
```

Inline (terminal tool):
```bash
cd /path/to/tool && PYTHONPATH= venv/Scripts/python -c "import torch"
```

---

## 13. WSL 2 — Діагностика та конвертація

Див. `references/wsl2-setup.md` — повний гайд: діагностика `HCS_E_HYPERV_NOT_INSTALLED`, увімкнення Hyper-V, конвертація WSL 1→2, автостарт Hermes після reboot через Task Scheduler.

## 14. Remote Access — AnyDesk + OpenSSH Server (Android/Phone)

### Коли потрібно

Користувач хоче керувати комп'ютером Windows **віддалено з телефона** (Android):

- **AnyDesk** — графічний робочий стіл (мишка/клавіатура), працює через релей-сервери без налаштування портів
- **OpenSSH Server** — термінальний доступ (через Termux на Android), для `hermes` CLI, скриптів, діагностики

### 14.1 AnyDesk — встановлення та налаштування

```powershell
# Скачати
Invoke-WebRequest -Uri "https://download.anydesk.com/AnyDesk.exe" -OutFile "$env:TEMP\AnyDesk.exe"

# Тиха установка з автозапуском
Start-Process -FilePath "$env:TEMP\AnyDesk.exe" -ArgumentList '--install "C:\Program Files\AnyDesk" --start-with-win --silent' -Wait -NoNewWindow

# Встановити пароль для unattended access
echo "YOUR_PASSWORD" | "C:\Program Files\AnyDesk\AnyDesk.exe" --set-password
```

**Отримати AnyDesk ID:**
```bash
grep "ad.anynet.id" "C:/ProgramData/AnyDesk/system.conf"
# → ad.anynet.id=1576333865
```

**На телефоні:** Play Market → AnyDesk → ввести ID → пароль

### 14.2 OpenSSH Server — встановлення

```powershell
# 1. Встановити компонент
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 2. Запустити та налаштувати автозапуск
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# 3. Firewall — відкрити порт 22
New-NetFirewallRule -DisplayName 'OpenSSH Server (sshd)' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow
```

**Перевірка:**
```powershell
Get-Service -Name sshd | Select-Object Name,Status,StartType
Get-NetFirewallRule -DisplayName 'OpenSSH*' | Select-Object DisplayName,Enabled
```

### 14.3 З'єднання з телефона (Termux)

```bash
# Termux (Android)
pkg install openssh
ssh USERNAME@LOCAL_IP
```

### 14.4 Tailscale — Mesh VPN (рекомендовано для SSH ззовні)

Tailscale створює захищений WireGuard-тунель між ПК і телефоном. Не потребує відкриття портів на роутері.

**Встановлення:**
```powershell
# Через winget (найпростіше)
winget install Tailscale.Tailscale --silent --accept-package-agreements
```

**Активація (одноразово):**
```bash
"C:/Program Files/Tailscale/tailscale.exe" up --accept-dns=false
# Видасть URL: https://login.tailscale.com/a/XXXXXXXXXXXX
# Користувач відкриває це посилання на телефоні, логіниться
```

**На телефоні:** Play Market → Tailscale → логін (той самий акаунт)

**Після підключення:**
- У Tailscale додатку на телефоні з'явиться IP ПК (вигляд `100.x.x.x`)
- SSH через Tailscale: `ssh PL_home@100.x.x.x`
- ПК доступний з будь-якої точки світу, навіть через мобільний інтернет

**Статус:**
```bash
tailscale status
tailscale ip -4
```

### 14.5 З'єднання ззовні домашньої мережі

| Інструмент | Як працює назовні | Налаштування |
|------------|:-----------------:|--------------|
| **AnyDesk** | ✅ Через релей-сервери, напряму | Не потребує портів |
| **Tailscale + SSH** | ✅ Через WireGuard тунель | Встановити Tailscale на ПК + телефон |
| **SSH (прямий)** | ❌ Потрібен port forwarding | Відкрити порт 22 на роутері |
| **Chrome Remote Desktop** | ✅ Через Google | Потребує логіну в браузері |

### 🚩 Важливо

- **shutdown /r** — заблоковано в Hermes (hardline block). Користувач має перезавантажити вручну.
- Після встановлення OpenSSH Server може знадобитись **перезавантаження** (`RestartNeeded: True`)
- AnyDesk пароль зберігається в `C:\\ProgramData\\AnyDesk\\system.conf` (зашифрований)
- Для входу через SSH використовується **логін і пароль Windows** користувача
- **AnyDesk ID** — зчитати з `grep "ad.anynet.id" "C:/ProgramData/AnyDesk/system.conf"`
- Для Tailscale важливо передати користувачу URL активації (`login.tailscale.com/a/...`) — він має відкрити його на телефоні

---

## 15. Hermes file tool path issues on Windows

### Проблема

`read_file`, `write_file`, `patch` — не розуміють MSYS шляхів (`/c/Users/...`). Вони конвертують їх неправильно:

| Передано | Фактично | Результат |
|----------|----------|-----------|
| `/c/Users/PL_home/file.txt` | `C:\c\Users\PL_home\file.txt` | ❌ Файл не знайдено |
| `C:\Users\PL_home\file.txt` | `C:\Users\PL_home\file.txt` | ✅ Працює |

Механізм: інструменти бачать `/c/` як Unix-префікс і дописують `C:\` перед ним → подвійне `c:\`.

### Фікс

У Hermes file tools (`read_file`, `write_file`, `patch`) завжди передавати **нативний Windows шлях** (`C:\Users\...` або `C:/Users/...`), НІКОЛИ MSYS (`/c/Users/...`).

```python
# ❌ НЕ ПРАЦЮЄ
patch(path="/c/Users/PL_home/file.txt", ...)
write_file(path="/c/Users/PL_home/.bashrc", ...)

# ✅ ПРАЦЮЄ
patch(path="C:\\Users\\PL_home\\file.txt", ...)
write_file(path="C:\\Users\\PL_home\\.bashrc", ...)
```

### terminal tool — навпаки

`terminal()` (git-bash) ПРАЦЮЄ з MSYS шляхами і ламається з Windows:
```bash
# ✅ В терміналі
source ~/.bashrc
ls /c/Users/PL_home/

# ❌ В терміналі може не спрацювати
ls C:\\Users\\PL_home  # зворотні слеші ламаються
ls C:/Users/PL_home    # прямі слеші — ок
```

Тому стандартний патерн:
- **terminal()** → MSYS шляхи (`/c/Users/...`)
- **read_file / write_file / patch** → Windows шляхи (`C:\Users\...`)

### python3 на Windows git-bash

`python3` на Windows git-bash часто веде до Windows Store заглушки (замість реального Python):
```
$ python3
nie znaleziono Python; uruchom bez argumentów, aby zainstalować
```

**Фікс:** використовувати `python` (якщо в PATH) або явний шлях до інтерпретатора. Обгортки на кшталт `~/.local/bin/ollama` мають посилатися на конкретний Python (uv-венв або системний), а не на `python3`.

### .bashrc та .bash_profile на git-bash

На Windows git-bash при першому запуску без `.bashrc` / `.bash_profile`:
```
WARNING: Found ~/.bashrc but no ~/.bash_profile, ~/.bash_login or ~/.profile.
This looks like an incorrect setup.
A ~/.bash_profile that loads ~/.bashrc will be created for you.
```

Всі три інструменти (write_file/patch/read_file) можуть їх створити/редагувати, але ТІЛЬКИ з нативним Windows шляхом.

```python
# Створення .bashrc
write_file(path="C:\\Users\\PL_home\\.bashrc",
           content='export PATH="$HOME/.local/bin:$PATH"\n')

# Створення .bash_profile, що завантажує .bashrc
write_file(path="C:\\Users\\PL_home\\.bash_profile",
           content='if [ -f "$HOME/.bashrc" ]; then\n    source "$HOME/.bashrc"\nfi\n')
```

---

## 16. BCD (Boot Configuration Data) — управління завантаженням

### Коли потрібно

- Додати другу ОС в меню завантаження (dualboot)
- Відновити завантажувач після збою
- Змінити порядок/час очікування в меню

### Читання поточного BCD

```cmd
bcdedit /enum          :: базові записи
bcdedit /enum all      :: всі записи (вкл. firmware, memory tester)
```

### Бекап перед змінами

```cmd
bcdedit /export C:\bcd_backup.bcd

:: Відновлення:
:: bcdedit /import C:\bcd_backup.bcd
```

### Додавання ОС вручну (коли bcdboot не працює)

`bcdboot` — стандартний інструмент, але **потребує прав адміністратора** і не завжди коректно додає запис для Windows 7 на UEFI/GPT.

**Крок 1: створити новий запис (через UAC)**
```powershell
# Запустити cmd як адмін, щоб отримати GUID
Start-Process cmd -Verb RunAs -ArgumentList '/c bcdedit /create /d "Windows 7" /application osloader > C:\result.txt 2>&1'
```
→ GUID вигляду `{ba433dc8-7892-11f1-b115-f756c29eac16}`

**Крок 2: налаштувати параметри завантаження**
```cmd
bcdedit /set {GUID} device partition=F:         :: розділ з ОС
bcdedit /set {GUID} path \Windows\system32\winload.efi
bcdedit /set {GUID} osdevice partition=F:       :: той самий розділ
bcdedit /set {GUID} systemroot \Windows
bcdedit /set {GUID} nx OptIn
bcdedit /set {GUID} detecthal Yes               :: важливо для Windows 7 UEFI!
bcdedit /displayorder {GUID} /addlast           :: додати в кінець меню
bcdedit /timeout 30                             :: час вибору (сек)
```

### Підвищення прав (UAC) через PowerShell

Оскільки `bcdedit` і `bcdboot` потребують адмін-прав, а `terminal` (git-bash) не може їх отримати напряму:

```powershell
# Тригер UAC — користувач клікає «Так»
Start-Process cmd -Verb RunAs -ArgumentList '/c команда > C:\Users\%USERNAME%\Desktop\result.txt 2>&1'
```

Альтернатива — scheduled task як SYSTEM (без UAC):
```powershell
schtasks /create /sc once /tn "TaskName" /tr "команда" /ru SYSTEM /rl HIGHEST /st 23:59 /f
schtasks /run /tn "TaskName"
```

### Особливості Windows 7 на UEFI/GPT

| Умова | Опис |
|-------|------|
| **winload.efi** | Має бути в `F:\Windows\system32\winload.efi`. Стандартний Windows 7 не має — потрібен патч (KB3087873) |
| **detecthal = Yes** | Обов'язково — інакше boot loader не знайде HAL |
| **Тип розділу** | GPT обов'язково, ESP (FAT32) має бути присутній |

### Перевірка результату

```cmd
bcdedit /enum
```

Очікуваний вивід — два Windows Boot Loader:
```
displayorder            {current}          ← Windows 11
                        {ba433dc8-...}     ← Windows 7
timeout                 30
```

---

## 17. System Optimization & Disk Cleanup

### ⚠️ RULE #1 (user-corrected 2026-07-11, refined 2026-07-12): ZAWSZE PYTAJ PRZED AKCJĄ

**Bezwzględna zasada — dotyczy WSZYSTKIEGO, nie tylko systemu:**
Przed KAŻDĄ operacją modyfikującą stan komputera użytkownika (deleting, moving, installing, config changes, copying files, renaming, creating folders) — **NAJPIERW POKAŻ CO BĘDZIESZ ROBIĆ I ZAPYTAJ O POZWOLENIE.**

**UA версія (користувач спілкується UA/EN/PL):**
Перш ніж ЩОСЬ зробити на комп'ютері користувача — завжди запитай. Навіть якщо здається очевидним. "Перш ніж щось зробити, пам'ятай завжди, потрібно мене запитати. Перш ніж виконувати." — пряма вказівка користувача.

**Три рівні перевірки перед дією:**

| Рівень | Питання | Приклад |
|--------|---------|---------|
| **1. Чи треба це робити?** | "Перенести ці папки в D:\Sorb\projekty?" | Користувач каже "перенеси все" — але треба уточнити, що саме "все" |
| **2. Що саме?** | "Всі три папки чи тільки наші проєкти?" | Користувач уточнив: тільки Hermes-івські проєкти, не його особисті файли |
| **3. Чи все правильно?** | Показати список файлів/папок перед виконанням | Показати, які саме файли будуть перенесені/видалені |

**Ключові патерни:**

1. **Навіть якщо завдання здається простим** — запитай. Move/delete/create — все потребує підтвердження.
2. **Уточнюй обсяг** — коли користувач каже "все" / "усе" / "wszystko", уточни, що саме мається на увазі. Наприклад: "перенеси все з робочого столу" → "всі файли чи тільки наші проєкти?"
3. **Показуй список перед дією** — навіть після отримання дозволу, покажи, що саме буде змінено.
4. **Якщо дія вже частково виконана** (як у цій сесії — часткове копіювання) — покажи поточний стан і запитай, як продовжити.
5. **Kiedy użytkownik mówi "dobre, wykonaj" / "robić" / "tak"** — nadal pokaż listę plików/kategorii przed faktycznym delete/move. Google Takeout 53 GB usunięte bez pokazania listy — użytkownik potrzebował tych plików.

**Kategoria operacji które ZAWSZE wymagają pytania:**
- Moving / copying plików między dyskami
- Deleting czegokolwiek (nawet pustych folderów)
- Instalowanie / odinstalowywanie oprogramowania
- Zmiany konfiguracji systemu
- Tworzenie folderów w lokalizacjach poza temp/workdir
- Zmiany powiązane z profilem użytkownika (desktop, documents, downloads)

**Co NIE wymaga pytania:**
- Operacje w K:\hermes_work\ (temp/workdir — bo to agent workspace)
- Odczyt plików (read_file, ls) — tylko jeśli nie zmienia stanu
- Tworzenie plików w hermetycznej przestrzeni roboczej (hermes_work)

**Zadania równoległe:** Gdy użytkownik daje drugie zadanie ("wątek") podczas gdy poprzednie jeszcze trwa — uruchamiaj w terminal(background) lub delegate_task. Nie blokuj się na jednym zadaniu.

---

### Kiedy robić

- Użytkownik prosi o "optymalizację systemu", "чистку дисків", "system optimization"
- C: >80%, F: >75%, dysk robi się pełny
- Przed instalacją nowego dużego oprogramowania

### Metodologia (w kolejności)

#### 1. Analiza — najpierw zrozum, potem czyść

Uruchom **równolegle** z długim timeoutem (≥180s).

**WARNING:** `du -sh` i `find ... -size` z git-bash/MSYS2 **timeoutują** na dyskach ≥500 GB przez NTFS/FUSE overhead. Zawsze używaj PowerShell `.ps1` skryptów dla głębokiej analizy:

```bash
# BEZPIECZNE (szybkie — tylko meta):
df -h /c/ /d/ /f/

# NIEBEZPIECZNE (timeoutują na dużych dyskach):
# du -sh /c/Users/...   # ← C: 310 GB → timeout
# find /c/ -size +500M  # ← timeout
```

**Zapisano w `references/disk-analysis-proven-patterns.md`: pełny przepis z PowerShell.**

```powershell
# PowerShell (.ps1) — skaluje się na dyski 500 GB+
# Zapisz do pliku, wykonaj: powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\script.ps1"

# TOP foldery (rekurencyjnie z sumą)
$results = @()
foreach ($dir in Get-ChildItem 'D:\' -Directory) {
    $size = (Get-ChildItem $dir.FullName -Recurse -File -EA 0 |
        Measure-Object -Property Length -Sum -EA 0).Sum
    $results += [PSCustomObject]@{Name=$dir.Name; SizeGB=[math]::Round($size/1GB,2)}
}
$results | Sort-Object SizeGB -Descending | Format-Table -AutoSize

# Duże pliki (>500 MB) — działa nawet na 500 GB+ dyskach
Get-ChildItem -Path 'C:\' -Recurse -File -EA 0 |
    Where-Object { $_.Length -gt 500MB } |
    Sort-Object Length -Descending |
    Select-Object @{N='Size(MB)';E={[math]::Round($_.Length/1MB)}}, FullName -First 20
```

**Dlaczego PowerShell zamiast bash:**

| Metoda | Czas na 500 GB NTFS | Działa? |
|--------|:-------------------:|:-------:|
| `find /c/ -size +500M` | Timeout (≥120s) | ❌ |
| `du -sh /c/Users/*` | Częściowy timeout | ⚠️ |
| PowerShell .ps1 (Get-ChildItem -Recurse) | ~60-180s | ✅ |
| `df -h` | Natychmiast | ✅ |

**Nie używaj inline `powershell.exe -Command` z bash** — bash rozbija `$_` / `{ }`. Zawsze pisz `.ps1` plik i wywołuj jako `-File`.

```bash
# Szybkie małe rzeczy (Temp, cache) — bash git-bash OK:
du -sh /c/Users/PL_home/AppData/Local/Temp
du -sh /c/Windows/Temp
du -sh "/c/Users/PL_home/AppData/Local/Google/Chrome/User Data/Default/Cache"
```

#### 2. Bezpieczne czyszczenie (zawsze pytaj przed czyszczeniem)

```bash
# Temp użytkownika + systemowy
rm -rf /c/Users/PL_home/AppData/Local/Temp/* 2>/dev/null
rm -rf /c/Windows/Temp/* 2>/dev/null

# Cache przeglądarek
rm -rf /c/Users/PL_home/AppData/Local/Google/Chrome/User\ Data/Default/Cache/*

# pip cache (Python)
pip cache purge

# Hermes audio cache
rm -f /c/Users/PL_home/AppData/Local/hermes/cache/audio/*.ogg

# Stare backupy configu Hermes
rm -f /c/Users/PL_home/AppData/Local/hermes/config.yaml.bak.*
```

#### 3. Duplicate file detection (bezpieczne — tylko analiza)

Znajdowanie duplikatów po nazwie+rozmiarze (szybka heurystyka, bez hashowania całych plików):

```powershell
# Duplikaty .exe w Program Files (po Name|Length)
$hash = @{}
foreach ($dir in @('C:\Program Files', 'C:\Program Files (x86)')) {
    Get-ChildItem -Path $dir -Recurse -File -Filter '*.exe' -EA 0 | ForEach-Object {
        $key = "$($_.Name)|$($_.Length)"
        if (-not $hash.ContainsKey($key)) { $hash[$key] = @() }
        $hash[$key] += $_.FullName
    }
}
$hash.Keys | ForEach-Object { if ($hash[$_].Count -gt 1) { 
    $parts = $_ -split '\|'
    [PSCustomObject]@{Name=$parts[0]; SizeMB=[math]::Round([int]$parts[1]/1MB,1); Count=$hash[$_].Count}
} } | Sort-Object Count -Descending | Select-Object -First 30 | Format-Table -AutoSize

# Duże instalujące pliki w Downloads (>50 MB)
$hash = @{}
Get-ChildItem -Path "$env:USERPROFILE\Downloads" -File -EA 0 | 
    Where-Object { $_.Length -gt 50MB } | ForEach-Object {
    $key = "$($_.Name)|$($_.Length)"
    if (-not $hash.ContainsKey($key)) { $hash[$key] = @() }
    $hash[$key] += $_.FullName
}
$hash.Keys | ForEach-Object { if ($hash[$_].Count -gt 1) { 
    $parts = $_ -split '\|'
    [PSCustomObject]@{Name=$parts[0]; SizeMB=[math]::Round([int]$parts[1]/1MB,1); Count=$hash[$_].Count; Paths=($hash[$_] -join "; ")} 
} } | Sort-Object Count -Descending | Format-Table -AutoSize
```

**Typowe rzeczy do znalezienia:**
- NVIDIA/Intel GPU drivers w Downloads (często 2+ wersje po ~800 MB)
- Docker Desktop installer (kilka wersji)
- MSI / producent-specific narzędzia
- Google Takeout archiwa splitowane na 10 GB części

| Obiekt | Lokalizacja | Typowy rozmiar | Uwagi |
|--------|-------------|----------------|-------|
| ESET/antivirus | AppData\Local\ESET + ProgramData\ESET | ~12 GB | Po odinstalowaniu — usuń wszystko |
| Playwright browsers | AppData\Local\ms-playwright | ~690 MB | Tylko jeśli nie używa testów |
| WinGet cache | AppData\Local\Temp\WinGet | ~2.4 GB | Cache menedżera pakietów |
| HuggingFace cache (whisper models) | ~/.cache/huggingface | ~5 GB | Після переходу на Groq/cloud STT — видалити всі whisper моделі |
| found.xxx | root dysku (np. F:\\found.000) | ~7 MB | Chkdsk recovery — można usuwać |
| hiberfil.sys | root dysku | 36+ GB | **SYSTEMOWY — NIE usuwać** |
| pagefile.sys | root dysku | 8+ GB | **SYSTEMOWY — NIE usuwać** |
| WSL disk | AppData\Local\wsl | ~6.5 GB | **NIE usuwać — systemowy** |

#### 5. PowerShell vs bash na Windows

**Terminal (git-bash/MSYS2):** proste rm działa na większości plików:
```bash
rm -rf /c/path/to/folder
```

**PowerShell (przez terminal z git-bash) — gdy `rm` failuje:**
```powershell
powershell.exe -Command "Get-ChildItem -Path 'C:\Path' -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
```

PowerShell lepiej radzi sobie z zablokowanymi plikami i długimi ścieżkami.

#### 6. Parallel execution pattern (user-corrected 2026-07-11)

The user corrected me: don't block on one task, use parallel execution.

```python
# In Hermes — use background + delegate_task for concurrent work
terminal(command="du -sh ...", background=True, notify_on_complete=True)
terminal(command="du -sh ...", background=True, notify_on_complete=True)

# For complex analysis — delegate to a subagent (fully independent)
delegate_task(goal="Find duplicates and large files on all disks", ...)

# Check progress while continuing conversation with user
process(action="poll", session_id="...")
```

#### 7. Cron daily system report

After optimization, offer to create a daily system report cron:

```python
cronjob(
    action="create",
    name="daily-system-report",
    schedule="0 10 * * *",  # 10:00 daily
    prompt="""
    Check: CPU load, RAM, disk usage (C:/D:/F/), network, Hermes version, STT/TTS status.
    Alerts: disk>80%, RAM<4GB, Hermes update available.
    Report in Ukrainian, concise, markdown table.
    """,
    deliver="origin"  # same chat
)
```

#### 8. CRITICAL: Always show list before delete — even when user says "do it"

**Pitfall from session 2026-07-11:** User said "Dobre, wykonaj" (go ahead), I deleted Google Takeout archives (53 GB) without showing the file list first. The user needed those files.

Rule: even when user says "go ahead" or "do it", ALWAYS:
1. Show the full file list with sizes
2. Describe what each category is
3. Get explicit confirmation per category before deleting

```python
# ❌ WRONG:
# user says "wykonaj" → immediately rm -rf

# ✅ RIGHT:
# "I found: takeout-20240223.zip (53 GB, 6 files), NVIDIA drivers (1.7 GB), Intel driver (877 MB)"
# "Delete each category? 1. Google Takeout? 2. Old drivers? ..."
# Wait for per-category confirmation.
```

**Categories that need confirmation:**
- Google Takeout archives — user may need them
- Downloads folder files — user wants to review
- Old GPU drivers — may be needed for rollback
- ESET quarantine — user may want to check what was flagged

**Categories safe to auto-clean (no confirmation needed):**
- Temp folders (user + system)
- Browser cache (Chrome, Edge)
- pip cache (Python)
- HuggingFace cache (after switching to cloud STT)
- found.xxx (chkdsk fragments)
- Hermes audio cache + old config backups

---

## 18. Запуск програм — спочатку перевірити чи вже працює

### Правило (user-corrected 2026-07-11)

**Перед запуском будь-якої програми — спочатку перевірити чи вона вже запущена.**

Якщо запустити програму, яка вже працює — вискочить "Błąd" (Windows помилка): "Instancja aplikacji XXX jest już uruchomiona."

### Перевірка

```bash
# через tasklist (git-bash)
tasklist //fi "IMAGENAME eq Greenshot.exe" 2>/dev/null | grep -c Greenshot
# → 0 = не запущена, 1+ = вже працює

# через PowerShell
powershell.exe -NoProfile -Command "Get-Process Greenshot -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"
```

### Патерн

```bash
count=$(tasklist //fi "IMAGENAME eq Program.exe" 2>/dev/null | grep -c Program)
if [ "$count" -eq 0 ]; then
  powershell.exe -Command "Start-Process 'C:\Path\To\Program.exe'"
else
  echo "Program вже запущено. Пропускаю."
fi
```

### Винятки

- Програми, які підтримують декілька інстанцій (Notepad++, VS Code, Chrome з різними профілями)
- Сервіси/демони без графічного інтерфейсу (вони не створюють "Błąd")

### 🚨 Pitfall: запуск GUI програм через subprocess ПРАВИЛЬНО

**❌ НЕ ПРАЦЮЄ (вікно не з'являється):**
```python
import subprocess
subprocess.Popen(['code', proj],
    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    close_fds=True)
```
`DETACHED_PROCESS` відриває GUI програму від робочого столу — процес запускається, але вікно не показується. Такий "zombie" процес блокує реальний запуск програми з помилкою "Another instance is already running as administrator".

**CRITICAL:** `CREATE_NO_WINDOW` / `DETACHED_PROCESS` → **ТІЛЬКИ для PowerShell/CMD** (через `silent_run.vbs`). Для GUI — **жодних флагів**, звичайний `subprocess.Popen` без `creationflags`.

**✅ ПРАЦЮЄ (через os.startfile):**
```python
import os
os.startfile(r'D:\\Sorb\\projekty')  # Відкриває папку в провіднику
os.startfile(r'C:\\path\\to\\Code.exe')  # Запускає програму
```

**✅ ПРАЦЮЄ (через subprocess без флагів):**
```python
import subprocess
proc = subprocess.Popen(['C:\\Path\\To\\Code.exe', 'D:\\project'], close_fds=True)
```

### 🧟 Zombie process detection — всі GUI apps

При запуску GUI програм через subprocess (навіть без флагів) може виникнути zombie — процес існує, але вікна нема. **Такий zombie блокує нормальний запуск програми користувачем.**

**Перевірка ВСІХ GUI apps на zombie (скрипт `hermes_diag.py` перевіряє 20+ додатків):**

```python
gui_apps = {
    'Code.exe': 'Visual Studio Code',
    'chrome.exe': 'Google Chrome',
    'firefox.exe': 'Mozilla Firefox',
    'brave.exe': 'Brave Browser',
    'WINWORD.EXE': 'Microsoft Word',
    'EXCEL.EXE': 'Microsoft Excel',
    'Telegram.exe': 'Telegram',
    'Discord.exe': 'Discord',
    'Spotify.exe': 'Spotify',
    # + більше в scripts/hermes_diag.py
}
```

**Детекція zombie:** кожний процес перевіряється через `MainWindowHandle` PowerShell:
```powershell
$p = Get-Process -Id {PID} -EA 0
if ($p -and $p.MainWindowHandle -ne 0) { "has_window" } else { "no_window" }
```

**Якщо жоден з процесів GUI app не має вікна → zombie → taskkill /F /IM.**

**Автоматичний монітор:** `scripts/proc_watchdog.py` запускається в фоні (через CREATE_NO_WINDOW + DETACHED_PROCESS для консолі) і кожні 2 сек перевіряє Code.exe, Chrome, Firefox, Word, Excel, Telegram. Якщо знаходить процеси без вікна — негайно вбиває.

## 19. KeePass (.kdbx) Database Merge

`skill_view("windows-system-administration", file_path="references/kdbx-merge-workflow.md")`

Full workflow: install KeePassXC CLI, find .kdbx databases across drives, merge with `keepassxc-cli merge` or pykeepass, pitfalls.

## 19. Pre-Update Backup — Hermes config staged update

**Перед кожним `hermes update` треба робити бекап конфігів та staged update з порівнянням 33 секцій config у 3 генераціях.**

### Чому це важливо

Hermes update може перезаписати `config.yaml`, скинути налаштування MCP серверів, terminal backend, skills, cron тощо. **Staged update procedure:**
1. Backup (pre_update_backup.py)
2. Download to separate test directory (D:\\Sorb\\hermes-update-test\\)
3. Compare config — 33 sekcje, 3 generacje (backup → current → new)
4. Risk analysis — 15+ protected keys
5. Apply if safe, block if risky

Повний опис: `skill_view(name="windows-system-administration", file_path="references/update-procedure.md")`

### Скрипти

**`scripts/pre_update_backup.py`**
```bash
python K:\hermes_work\pre_update_backup.py
python K:\hermes_work\pre_update_backup.py compare
```

**`scripts/hermes_update_check.py`** (також запускається cron `nightly-update-check` о 1:00)
```bash
python K:\hermes_work\hermes_update_check.py
```

## Norton 360 Log Analysis

Norton детекції та autosandbox логи знаходяться в `C:\\\\ProgramData\\\\Norton\\\\Antivirus\\\\log\\\\`. Два ключових файли:
- `detections.log` — всі спрацювання (browserPasswordDetection, virusMultiDetection, FileSystemShield)
- `autosandbox.log` — кандидати на пісочницю (формат UTF-16LE!)

`references/norton-log-analysis.md` — повний гайд по читанню та аналізу логів.

## Gateway Restart Loop & "Agent Not Responding" Diagnostics

Коли після рестарту комп'ютера Hermes перестає відповідати в Telegram — причиною часто є **gateway restart loop** через `[WinError 5] Odmowa dostępu` при self-restart. Norton 360 блокує spawn Python процесів від звичайного користувача.

`references/gateway-restart-loop-diagnostics.md` — діагностика, виправлення (SYSTEM-level elevated scheduled task — найефективніше), Norton exclusions, startup order (Hindsight → Gateway), перевірка та pitfalls.

## BIOS Virtualization & WSL 2

**Ключова діагностика:**
```powershell
Get-CimInstance -ClassName Win32_Processor | Select-Object VirtualizationFirmwareEnabled
# → False = BIOS VT-x/AMD-V вимкнено
```

Якщо `VirtualizationFirmwareEnabled=False` — WSL 2 не працюватиме навіть при встановлених Windows Features (Hyper-V, Virtual Machine Platform). Потрібно увімкнути в BIOS/UEFI:
1. Перезавантажити → F2/Del/F10
2. Advanced → CPU Configuration → Intel Virtualization Technology (VT-x) або SVM Mode (AMD)
3. Enabled → Save & Exit

`references/wsl2-setup.md` — повний гайд діагностики та конвертації.

## GitHub English-Only Convention

`skill_view("windows-system-administration", file_path="references/github-english-convention.md")`

User rule: ALL GitHub content (descriptions, commits, docs, metadata) must be **English only** — private repos included. Reference file has fix procedures for existing non-English content.

## Джерела

- [Microsoft Windows Security Documentation](https://learn.microsoft.com/en-us/windows/security/)
- [Microsoft Security Compliance Toolkit](https://learn.microsoft.com/en-us/windows/security/operating-system-security/system-security/windows-security-baseline)
- [CIS Benchmarks for Windows](https://www.cisecurity.org/benchmark/microsoft_windows_desktop)
- [Microsoft PowerShell Documentation](https://learn.microsoft.com/en-us/powershell/)
