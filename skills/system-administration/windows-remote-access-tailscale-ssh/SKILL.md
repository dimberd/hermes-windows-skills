---
name: windows-remote-access-tailscale-ssh
description: "Віддалений доступ до Windows ПК через Tailscale SSH — без OpenSSH Server, без паролів, без налаштування роутера."
category: system-administration
---

# Tailscale SSH — доступ ТІЛЬКИ до Linux/macOS серверів

**ВАЖЛИВО:** Tailscale SSH працює як SSH-сервер **тільки на Linux та macOS**. На **Windows** Tailscale SSH працює **тільки як клієнт** — з Windows можна підключатись до інших машин, але **Windows НЕ може приймати Tailscale SSH**.

## Де Tailscale SSH працює як сервер?

| Платформа | Може бути SSH-сервером | Може бути SSH-клієнтом |
|-----------|----------------------|-----------------------|
| Linux     | ✅ Так               | ✅ Так |
| macOS     | ✅ Так (tailscaled)  | ✅ Так |
| Windows   | ❌ **Ні**            | ✅ Так |

*Джерело: [Tailscale Docs — Tailscale SSH](https://tailscale.com/kb/1193/tailscale-ssh)*

## Для Windows — як налаштувати SSH-доступ

Оскільки Tailscale SSH не працює як сервер на Windows, потрібен **OpenSSH Server**:

### 1. Встановити OpenSSH Server на цільовому Windows ПК

```powershell
# PowerShell від адміністратора
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service -Name sshd -StartupType 'Automatic'
Start-Service sshd
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

### 2. Tailscale забезпечує мережу (замість портів на роутері)

OpenSSH Server слухає на локальному IP (127.0.0.1 або локальній мережі).
Tailscale забезпечує безпечний тунель — не потрібно відкривати порти на роутері.

### 3. Підключення

```powershell
ssh username@<tailscale-ip-цільового-пк>
```

## Коли використовувати RDP замість SSH

Для Windows-to-Windows частіше використовують **RDP через Tailscale**:

```powershell
# На цільовому ПК (від адміністратора)
# RDP вже має бути ввімкнено
# Підключення:
mstsc /v:<tailscale-ip>
```

## Підсумок

- **Windows → Linux/macOS сервер** — Tailscale SSH (`tailscale up --ssh` на сервері)
- **Windows → Windows** — OpenSSH Server + Tailscale, або RDP через Tailscale
- **Tailscale SSH не замінює OpenSSH Server на Windows**
