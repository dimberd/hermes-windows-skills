---
name: windows-remote-access-setup
description: "Налаштування віддаленого доступу до Windows ПК: AnyDesk, OpenSSH Server, Tailscale VPN. Для керування з телефона (Android) через Termux, AnyDesk або Tailscale."
version: 1.0.0
author: Dima + Hermes Agent
---

# Windows Remote Access Setup

## Коли використовувати

- Користувач хоче керувати ПК з телефона
- Потрібен віддалений доступ (консоль + графіка)
- Налаштування SSH, AnyDesk, Tailscale

## Спосіб: AnyDesk + OpenSSH + Tailscale

### 1. AnyDesk (графічний доступ)

```powershell
# Завантажити
Invoke-WebRequest -Uri "https://download.anydesk.com/AnyDesk.exe" -OutFile "$env:TEMP\AnyDesk.exe" -UseBasicParsing

# Встановити
Start-Process -FilePath "$env:TEMP\AnyDesk.exe" -ArgumentList "--install `"C:\Program Files\AnyDesk`" --start-with-win --silent" -Wait -NoNewWindow

# Дізнатись ID
Get-Content "$env:ProgramData\AnyDesk\system.conf" | Select-String "ad.anynet.id"

# Встановити пароль (unattended access)
echo "PASSWORD" | "C:/Program Files/AnyDesk/AnyDesk.exe" --set-password
```

**AnyDesk ID:** в `ad.anynet.id` у `C:\ProgramData\AnyDesk\system.conf`

### 2. OpenSSH Server (консольний доступ)

```powershell
# Встановити
Add-WindowsCapability -Online -Name "OpenSSH.Server~~~~0.0.1.0"

# Запустити
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# Фаєрвол
New-NetFirewallRule -DisplayName "OpenSSH Server (sshd)" -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow
```

Після цього з телефона:
```bash
# Termux
pkg install openssh
ssh Користувач@IP_ПК
```

### 3. Tailscale (VPN — безпечний доступ ззовні)

> ⚠️ **Tailscale SSH does NOT work as server on Windows.** Tailscale SSH server component is available only on Linux and macOS. On Windows, Tailscale SSH works only as client (connecting to other machines). For Windows-to-Windows SSH, use OpenSSH Server (section 2).
>
> → See `references/tailscale-ssh-official-docs.md` for official source and details.

#### Встановлення
```bash
winget install Tailscale.Tailscale --silent --accept-package-agreements
```

#### Активація
```bash
"C:\Program Files\Tailscale\tailscale.exe" up
# Видасть URL для авторизації
```

#### CLI — статус та IP
```bash
tailscale status            # список пристроїв в мережі
tailscale ip -4             # свій Tailscale IP
tailscale ping 100.x.x.x    # перевірка з'єднання
```

### 4. Agent-mediated remote diagnostics (Hermes на ПК третьої особи)

**Коли потрібно:** користувач просить Hermes підключитись до ПК іншої людини (брата, друга, клієнта) через Tailscale + SSH для CLI-діагностики.

**Схема:** ПК третьої особи ←Tailscale P2P→ ПК користувача (Hermes) → Telegram

**Workflow:**

1. На ПК користувача згенерувати Ed25519 ключ:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/hermes_remote_key -N "" -C "hermes-remote-access"
   cat ~/.ssh/hermes_remote_key.pub
   ```

2. Інструкція для віддаленого ПК:
   - Встановити Tailscale, залогінитись
   - В PowerShell (Admin):
     ```powershell
     Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
     Start-Service sshd
     Set-Service -Name sshd -StartupType Automatic
     New-Item -Type Directory -Force $env:USERPROFILE\.ssh
     Add-Content $env:USERPROFILE\.ssh\authorized_keys "ssh-ed25519 AAA..."
     ```
   - Повідомити свій Tailscale IP

3. Підключення Hermes:
   ```bash
   ssh USERNAME@100.x.x.x -i ~/.ssh/hermes_remote_key
   ```

4. Діагностика через SSH:
   - Get-WinEvent — критичні помилки System/Application
   - sfc /scannow + DISM
   - chkdsk C: /f
   - BSOD дампи, драйвери, оновлення

**Нюанси:**
- Tailscale P2P пробиває NAT — не треба портів на роутері
- SSH-ключ без passphrase
- Windows-акаунт має мати пароль
- Публічний ключ зберігати в файлі на Desktop
- Альтернатива: RustDesk (графічний, ID+пароль)

### 5. Збереження параметрів у файл на робочий стіл

Створити текстовий файл з усіма даними:
- AnyDesk ID + пароль
- SSH: хост, порт, користувач
- Tailscale: посилання для активації
- Інструкція для Termux команд

Зберігати в `C:\Users\%USERNAME%\Desktop\HERMES_REMOTE_ACCESS.txt`

### Важливі нюанси

1. **OpenSSH Server** — спочатку статус `Staged`, після встановлення треба `RestartNeeded: True`
2. **AnyDesk пароль** — використовувати `openssl rand -base64 12 | tr -dc 'A-Za-z0-9!@#$' | head -c 16` для генерації
3. **Tailscale up** — чекає поки користувач відкриє URL в браузері. Не вбивати процес!
4. **WSL 2 потребує** Hyper-V + VirtualMachinePlatform + HypervisorPlatform + рестарт ПК
5. **Scheduled Task for startup** — `New-ScheduledTaskTrigger -AtStartup`, `User "PL_home" -RunLevel Highest`, S4U logon (не потребує пароля)
6. **Для WSL 2 конвертації з scheduled task** — краще робити через PowerShell скрипт з `wsl --set-version Ubuntu-26.04 2`
7. **AnyDesk silent install** — `--install "C:\Program Files\AnyDesk" --start-with-win --silent`
