---
name: windows-wsl2-conversion-and-autostart
description: "Налаштування Windows -> WSL 2 конвертація + Hyper-V увімкнення + scheduled task для автозапуску скриптів після рестарту системи. Працює без входу користувача (S4U logon)."
version: 1.2.0
author: Dima + Hermes Agent
---

# Windows WSL 2 Conversion & Post-Boot Automation

## Коли використовувати

- Потрібно конвертувати WSL 1 дистрибутив у WSL 2
- Потрібно увімкнути Hyper-V компоненти
- Потрібен автозапуск скриптів/сервісів після завантаження Windows (без логіну користувача)
- Віддалене керування — користувач не біля компа
- **HCS_E_HYPERV_NOT_INSTALLED** помилка при спробі конвертації

## Перевірка статусу

```bash
# Статус WSL (через tr щоб прибрати null-байти UTF-16 з git-bash)
wsl -l -v | tr -d '\000'

# Статус WSL через PowerShell (чистіше)
powershell -NoProfile -Command "wsl -l -v"

# Статус Hyper-V компонентів (з git-bash/MSYS треба повний шлях!)
/c/Windows/System32/dism.exe /online /get-features /format:table | grep -i hyper

# CPU віртуалізація
/c/Windows/System32/systeminfo.exe | grep -i "hyper-v\|virtualization"

# HyperVisor присутній?
powershell -NoProfile -Command "Get-ComputerInfo -Property 'HyperV*'"

# Boot configuration — hypervisorlaunchtype має бути Auto
# Через powershell -NoProfile -Command "bcdedit ..." НЕ ПРАЦЮЄ (encoding issue)
# Правильно:
/c/Windows/System32/bcdedit.exe /enum {current} | grep -i hypervisor
# Або:
cmd.exe /c "bcdedit /enum {current}" | grep -i hypervisor
```

## ❗ Відомі проблеми git-bash з WSL командами

### 1. `wsl -l -v` показує кракозябри (null-байти UTF-16)

Вивід `wsl.exe` через git-bash має null-байти між символами. Рядок виглядає як:
```
\u0000*\u0000 \u0000U\u0000b\u0000...
```
**Фікс:** `| tr -d '\000'` або PowerShell:
```bash
wsl -l -v | tr -d '\000'
powershell -NoProfile -Command "wsl -l -v"
```

### 2. `wsl ~` ламається (tilde expansion)

Git-bash розширює `~` в Windows-шлях `/c/Users/<user>`, який WSL не розуміє:
```bash
# ❌ НЕ ПРАЦЮЄ
wsl ~ -e lsb_release -a
# → /c/Users/PL_home: No such file or directory

# ✅ ПРАЦЮЄ — вказувати дистрибутив явно
wsl -d Ubuntu-26.04 -e cat /etc/os-release
```

### 3. `bcdedit` через PowerShell падає з помилкою encoding

```bash
# ❌ НЕ ПРАЦЮЄ — PowerShell додає /encodedCommand
powershell -NoProfile -Command "bcdedit /enum {current}"
# → Invalid command line switch: /encodedCommand

# ✅ ПРАЦЮЄ
/c/Windows/System32/bcdedit.exe /enum {current}
cmd.exe /c "bcdedit /enum {current}"
```

## Увімкнення Hyper-V для WSL 2

**ВАЖЛИВО:** З git-bash/MSYS команда `dism` не працює без повного шляху. Треба:

```bash
# Правильно (git-bash)
/c/Windows/System32/dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V /all /quiet /norestart
/c/Windows/System32/dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /quiet /norestart

# Або через PowerShell
powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All"
powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All"
```

**Необхідні компоненти (всі мають бути Enabled):**
- `Microsoft-Hyper-V-Hypervisor`
- `Microsoft-Hyper-V-Services`
- `VirtualMachinePlatform`
- `Microsoft-Hyper-V-Management-PowerShell` (опціонально)

**Потрібен рестарт ПК після enable.**

## Конвертація дистрибутива на WSL 2

```bash
# Перед конвертацією — оновити WSL
wsl --update

# Спробувати з PowerShell (деколи працює краще ніж з git-bash)
powershell -Command "wsl --set-version Ubuntu-26.04 2"

# Або встановити WSL 2 як default для нових дистрибутивів
wsl --set-default-version 2
```

## Діагностика HCS_E_HYPERV_NOT_INSTALLED

Ця помилка виникає коли Hyper-V компоненти увімкнені, але WSL 2 все одно не конвертується.

**Головна причина:** прихований `RebootPending` в Component-Based Servicing — компоненти встановлені (`Enabled`) але не активовані. Навіть після rebootу система може вимагати ще одного, якщо Hyper-V встановлювався частинами.

### Перевірка pending reboot (найважливіше!)

```bash
# Перевірити чи є прихований pending reboot
powershell -Command "Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'"
# Повертає True — потрібен ще один reboot!
```

Якщо `True` — жодні маніпуляції з WSL/Hyper-V не допоможуть, поки система не перезавантажиться ще раз. Це найчастіша причина HCS_E_HYPERV_NOT_INSTALLED після того як всі компоненти увімкнено.

### Порядок дій:

1. **Перевірити чи всі Hyper-V компоненти увімкнені:**
   ```bash
   /c/Windows/System32/dism.exe /online /get-features /format:table | grep -i "hyper-v\|vm\|virtual"
   ```

2. **Перевірити hypervisorlaunchtype:**
   ```bash
   /c/Windows/System32/bcdedit.exe /enum {current} | grep -i hypervisorlaunchtype
   ```
   Має бути `Auto`. Якщо `Off` — виправити:
   ```bash
   bcdedit /set hypervisorlaunchtype auto
   ```

3. **Оновити WSL:**
   ```bash
   wsl --update
   ```

4. **Зробити shutdown WSL та спробувати знову:**
   ```bash
   wsl --shutdown
   wsl --set-version Ubuntu-26.04 2
   ```

5. **Перевірити Hyper-V Compute Service (HCS):**
   ```bash
   powershell -Command "Get-Service -Name 'HvHost','vmms','vmicvmsession' | Select-Object Name,Status"
   ```
   HvHost та vmms мають бути Running.

6. **Перевірити Windows Defender Credential Guard:**
   ```bash
   powershell -Command "Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard | Select-Object VirtualizationBasedSecurityStatus, SecurityFeaturesEnabled"
   ```
   VBS = 2 означає Enabled.

### Якщо все одно не працює:

0. **Перевірити pending reboot (90% випадків!):**
   ```bash
   powershell -NoProfile -Command "Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending'"
   ```
   Якщо `True` → потрібен **останній reboot**, і все запрацює. Користувач може зробити кілька rebootів але pending не знімається. Перевіряти після КОЖНОГО rebootу.

1. **Якщо pending reboot False, але WSL2 все одно не конвертується:**
   - **Cold boot (холодний старт)** — Windows Fast Startup може не завантажити гіпервізор навіть після reboot. Спробувати **Shut down (затиснути Shift)** або `shutdown /s /t 0` замість Restart. Це робить повний старт ядра і Hyper-V має завантажитись.
   - Відкрити термінал (cmd.exe) від адміністратора:
     ```cmd
     shutdown /s /t 0
     ```
     Потім увімкнути ПК знову.

2. **BIOS/UEFI** — перевірити що віртуалізація (Intel VT-x / AMD SVM) увімкнена:
   ```bash
   # PowerShell перевірка BIOS VT-x
   powershell -NoProfile -Command "Get-CimInstance Win32_Processor | Select-Object Name, VirtualizationFirmwareEnabled"
   ```
   Якщо `VirtualizationFirmwareEnabled = False` → зайти в BIOS (F2/Del при старті) → увімкнути Intel Virtualization Technology / SVM Mode.

3. **Конкуруючий гіпервізор** — VMWare, VirtualBox, або інший гіпервізор може блокувати Hyper-V:
   ```bash
   powershell -NoProfile -Command "Get-WmiObject -Class Win32_ComputerSystem | Select-Object HypervisorPresent"
   ```
   Якщо `HypervisorPresent = True` але Hyper-V не працює — можливо інший гіпервізор зайняв VT-x.

4. **Core Isolation / Memory Integrity** — може блокувати Hyper-V. Вимкнути в Windows Security → Device Security → Core Isolation

5. **Windows Insider Build** — на builds 26200+ (24H2 Preview) відома проблема HCS_E_HYPERV_NOT_INSTALLED. Можливе рішення: дочекатись оновлення або встановити стабільну версію Windows

### Альтернатива: Docker Desktop

Якщо WSL 2 не вдається ввімкнути (навіть після всіх rebootів), Docker Desktop можна встановити напряму:

**Встановлення:**
```bash
# 1. Завантажити (або вручну з https://docs.docker.com/desktop/setup/install/windows-install/)
curl -skL -o /tmp/DockerDesktop.exe https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe

# 2. Встановити (ВАЖЛИВО: напряму, не через start /wait!)
"/c/Users/<USER>/Downloads/DockerDesktop.exe" install --quiet --accept-license

# 3. Запустити службу
powershell -Command "Start-Service com.docker.service"

# 4. Docker CLI шлях (git-bash/MSYS не додає його в PATH автоматично)
/c/Program\ Files/Docker/Docker/resources/bin/docker.exe --version
```

**ВАЖЛИВО:** Docker Desktop теж потребує Hyper-V. Якщо HCS_E_HYPERV_NOT_INSTALLED не вирішено, Docker engine не запуститься. Лікується тим же pending reboot або відкатом до стабільної версії Windows.

## Scheduled Task для автозапуску після рестарту (без логіну)

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\hermes_startup.ps1`""
$trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay "00:00:20"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit "00:10:00"

Register-ScheduledTask -TaskName "MyPostBootTask" -Action $action -Trigger $trigger -User "%USERNAME%" -RunLevel Highest -Settings $settings -Force
```

**Ключові моменти:**
- `-User "%USERNAME%"` — запускається як користувач (S4U logon), не потребує пароля
- `-LogonType Interactive` НЕ використовувати — це вимагає входу в систему
- `-AtStartup` а не `-AtLogOn` — запуск при старті Windows, не при вході
- `-ExecutionTimeLimit` — обмеження часу виконання

## Приклад startup скрипта (hermes_startup.ps1)

```powershell
Start-Sleep -Seconds 15    # Чекаємо систему

# WSL 2 конвертація
wsl --set-version Ubuntu-26.04 2

# PATH для сервісів
$env:Path = "C:\Users\%USERNAME%\AppData\Local\hermes\hermes-agent\venv\Scripts;" + $env:Path

# Запуск сервісу (приклад)
Start-Process -FilePath "powershell.exe" -ArgumentList "-WindowStyle Hidden ..." -PassThru
```

## Важливі нюанси

1. **Hyper-V увімкнення** — `dism /online /enable-feature` в git-bash не працює (command not found). Треба повний шлях `/c/Windows/System32/dism.exe` або PowerShell
2. **shutdown заблокований** — Hermes не дає shutdown/reboot через агента (hard blocklist). Повідомити користувача зробити вручну
3. **S4U logon** — User S4U дозволяє scheduled task працювати без пароля і без інтерактивного входу
4. **Sleep після старту** — обов'язково чекати 15-20 секунд, щоб система та WSL ініціалізувались
5. **Перевірка статусу після рестарту** — через Telegram або логи: `$env:USERPROFILE\\hermes_startup.log`
6. **WSL 2 потребує** `VirtualMachinePlatform` + `HypervisorPlatform` + `Microsoft-Hyper-V-Hypervisor` — всі три мають бути Enabled
7. **Кілька rebootів** — інколи Hyper-V потребує 2 rebootи: перший для встановлення компонентів, другий для активації hypervisorlaunchtype
8. **Cold boot** — якщо після rebootу pending reboot = False, але WSL2 все одно не конвертується, спробувати `shutdown /s /t 0` (повне вимкнення) замість Restart. Fast Startup може не завантажити гіпервізор.
9. **dism з git-bash** — завжди використовувати `/c/Windows/System32/dism.exe` або `cmd.exe /c "dism ..."`, ніколи просто `dism`
10. **wsl.exe вивід** — через git-bash вивід wsl.exe має UTF-16 null-байти, що засмічує термінал. Використовувати `tr -d '\000'` або PowerShell для читання
11. **wsl ~ не працює** — з git-bash `wsl ~ -e command` ламається через tilde expansion. Завжди використовувати `wsl -d <distro> -e command`
12. **bcdedit encoding** — `powershell -NoProfile -Command "bcdedit /enum {current}"` падає з помилкою /encodedCommand. Використовувати `/c/Windows/System32/bcdedit.exe` напряму
13. **Конкуруючий гіпервізор** — VMWare/VirtualBox можуть зайняти VT-x і блокувати Hyper-V. Перевіряти `Get-CimInstance Win32_Processor | Select VirtualizationFirmwareEnabled`
