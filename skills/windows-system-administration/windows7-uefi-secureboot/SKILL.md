---
name: windows7-uefi-secureboot
description: |-
  Додавання Windows 7 до BCD Windows 11 для Dual Boot з UEFI+GPT,
  підписування boot файлів Windows 7 самопідписаним сертифікатом
  для сумісності з Secure Boot (10 років).
version: 1.2.0
platforms: [windows]
metadata:
  hermes:
    tags: [windows, uefi, secure-boot, bcd, dual-boot, windows-7]
    category: windows-system-administration
---

# Windows 7 UEFI + Secure Boot Dual Boot

## Призначення
Додати Windows 7 (GPT/UEFI) до завантажувального меню Windows 11 та забезпечити сумісність із Secure Boot через підписування boot файлів самопідписаним сертифікатом.

## Передумови
- Windows 7 має бути встановлений на GPT-диску з UEFI-завантажувачем
- Windows 7 повинен мати `bootmgfw.efi` та `winload.efi` (патч KB3087873)
- Windows 11 встановлений окремо (на іншому диску або розділі)
- Потрібен **адмін-доступ** (UAC)
- Для enrollment сертифіката: USB флешка FAT32

## Дискова структура (типова)
```
Диск 0 — Samsung NVMe (Boot Disk)
  ├─ ESP (FAT32 100MB) ← активний ESP Windows 11
  ├─ C: (499GB)       ← Windows 11
  └─ D: (1362GB)      ← Дані

Диск 2 — SSDPR-CX400 (SATA SSD)
  ├─ F: (201GB)       ← Windows 7
  └─ ESP (FAT32 100MB) ← неактивний ESP
```

## ⚠️ ВАЖЛИВО: Самопідписаний сертифікат — обмеження

**Навіть після успішного enrollment сертифіката в UEFI Secure Boot db, Windows Boot Manager (bootmgfw.efi) може відхилити winload.efi з помилкою 0xc0000428.**

Чому: Windows bootmgfw.efi має **власний внутрішній список довірених сертифікатів** (Microsoft кореневі CA, вбудовані в бінарник). Самопідписаний сертифікат там не значиться → `0xc0000428: The digital signature for this file couldn't be verified`.

**Ланцюжок перевірки:**
1. UEFI firmware → перевіряє bootmgfw.efi → знаходить сертифікат в db → ✅ PASS
2. bootmgfw.efi → завантажує winload.efi → перевіряє підпис через СВІЙ список → ❌ FAIL (якщо підписано нашим cert)

**Рішення:** Якщо custom cert дає 0xc0000428 — відновити оригінальний MS-підпис і використовувати CSM (крок 8).

## ⚠️ Ключовий крок: визначення активного ESP

У системі може бути **кілька ESP** (по одному на кожному GPT-диску). Важливо редагувати ТОЙ ESP, з якого реально завантажується система.

```cmd
mountvol S: /s
bcdedit /store S:\EFI\Microsoft\Boot\BCD /enum
```

`mountvol S: /s` монтує ESP поточного завантажувального диска. Якщо після зміни BIOS (напр. CSM→UEFI) система завантажується з іншого ESP — BCD там буде іншим, без Windows 7.

**Після зміни BIOS режиму (CSM↔UEFI) — ЗАВЖДИ перевіряти активний ESP наново.**

## Кроки

### 1. Просканувати диски
```cmd
echo list disk | diskpart
```

Детально:
```
select disk 0
detail disk
list partition
select disk 2
detail disk
list partition
```
Запустити: `diskpart /s <script>.txt`

### 2. Додати Windows 7 до BCD

**ВИЗНАЧИТИ правильний ESP спочатку (крок ⚠️ вище).** `bcdedit` без `/store` завжди пише в активний BCD — це те, що нам треба.

```cmd
bcdedit /create /d "Windows 7" /application osloader
```
Зберегти отриманий GUID, потім:
```cmd
bcdedit /set {GUID} device partition=F:
bcdedit /set {GUID} path \Windows\system32\winload.efi
bcdedit /set {GUID} osdevice partition=F:
bcdedit /set {GUID} systemroot \Windows
bcdedit /set {GUID} nx OptIn
bcdedit /set {GUID} detecthal Yes
bcdedit /displayorder {GUID} /addlast
bcdedit /timeout 30
```

**Важливо:** `/create` **НЕ ПРАЦЮЄ** з параметром `/store`. Якщо треба створити запис у BCD на неактивному ESP — скопіювати BCD, змінити через SYSTEM, скопіювати назад.

### 3. Виконання з адмін-правами

```powershell
Start-Process cmd -Verb RunAs -ArgumentList '/c bcdboot F:\Windows /f UEFI /l pl-PL > C:\Users\%USERNAME%\Desktop\result.txt 2>&1'
```
Користувач має клікнути «Так» на UAC щоразу.

**Для серії команд:** створити .cmd файл, запустити його через `Start-Process -Verb RunAs` — один UAC на всі команди.

### 4. Перевірка BCD
```cmd
bcdedit /enum
```
Має показати два Windows Boot Loader:
- `{current}` → Windows 11 (C:\)
- новий GUID → Windows 7 (F:\) з `detecthal = Yes`

### 5. Підписування boot файлів для Secure Boot

Windows 7 має підписи Microsoft (`MS Windows Verification PCA`), але сертифікати протерміновані (до 2019-2020). Secure Boot на сучасних UEFI може їх блокувати.

**Рішення:** створити самопідписаний сертифікат на 10 років, підписати boot файли, додати сертифікат в UEFI db.

#### 5.1 Бекап
```cmd
copy "F:\Windows\Boot\EFI\bootmgfw.efi" "F:\Windows\Boot\EFI\bootmgfw.efi.bak"
copy "F:\Windows\System32\winload.efi" "F:\Windows\System32\winload.efi.bak"
```

#### 5.2 Створити сертифікат (як звичайний користувач)
```powershell
$cert = New-SelfSignedCertificate -Type CodeSigningCert `
    -Subject "CN=Windows 7 UEFI SecureBoot, O=Custom" `
    -FriendlyName "Windows 7 Secure Boot Certificate" `
    -NotAfter (Get-Date).AddYears(10) `
    -CertStoreLocation "Cert:\CurrentUser\My"

Export-Certificate -Cert $cert -FilePath "$env:USERPROFILE\Desktop\Win7BootCert.cer" -Type CERT

# DER і PEM формати — на всяк випадок (MSI BIOS іноді вимагає DER)
$derBytes = $cert.RawData
[System.IO.File]::WriteAllBytes("$env:USERPROFILE\Desktop\Win7BootCert.der", $derBytes)

$pem = @"
-----BEGIN CERTIFICATE-----
$([Convert]::ToBase64String($derBytes, [System.Base64FormattingOptions]::InsertLineBreaks))
-----END CERTIFICATE-----
"@
$pem | Out-File -FilePath "$env:USERPROFILE\Desktop\Win7BootCert.pem" -Encoding ascii
```

#### 5.3 Підписати файли через SYSTEM (найнадійніший спосіб)

**Проблема:** звичайний адмін не може писати в `C:\Windows\Boot\EFI\` та `C:\Windows\System32\`. Навіть `takeown` + `icacls` не завжди працюють з PowerShell.

**Рішення — SYSTEM scheduled task:**

```cmd
REM 1. Export PFX (щоб SYSTEM міг імпортувати сертифікат)
powershell -Command "$pwd = ConvertTo-SecureString -String 'boot1234' -Force -AsPlainText; Export-PfxCertificate -Cert $cert -FilePath '$env:USERPROFILE\Desktop\Win7BootCert.pfx' -Password $pwd"

REM 2. Створити скрипт sign.cmd:
@echo off
REM Створюємо сертифікат в LocalMachine (доступний SYSTEM)
powershell -NoProfile -Command ^
  "$pwd = ConvertTo-SecureString -String 'boot1234' -Force -AsPlainText;" ^
  "Import-PfxCertificate -FilePath 'C:\Users\PL_home\Desktop\Win7BootCert.pfx' -CertStoreLocation 'Cert:\LocalMachine\My' -Password $pwd > nul"

REM Копіюємо файли в тимчасову теку (куди SYSTEM має доступ)
mkdir C:\Windows\Temp\bootsign 2>nul
copy /y "F:\Windows\Boot\EFI\bootmgfw.efi" "C:\Windows\Temp\bootsign\bootmgfw.efi"
copy /y "F:\Windows\System32\winload.efi" "C:\Windows\Temp\bootsign\winload.efi"

REM Підписуємо копії (в LocalMachine немає захисту)
powershell -NoProfile -Command ^
  "$cert = Get-ChildItem -Path Cert:\LocalMachine\My -CodeSigningCert | Where-Object { $_.Subject -like '*Windows 7*' } | Select-Object -First 1;" ^
  "$r1 = Set-AuthenticodeSignature -FilePath 'C:\Windows\Temp\bootsign\bootmgfw.efi' -Certificate $cert -IncludeChain All -Force -HashAlgorithm SHA256;" ^
  "$r2 = Set-AuthenticodeSignature -FilePath 'C:\Windows\Temp\bootsign\winload.efi' -Certificate $cert -IncludeChain All -Force -HashAlgorithm SHA256"

REM Замінюємо оригінали підписаними копіями
takeown /f "F:\Windows\Boot\EFI\bootmgfw.efi" /a
icacls "F:\Windows\Boot\EFI\bootmgfw.efi" /grant SYSTEM:F
copy /y "C:\Windows\Temp\bootsign\bootmgfw.efi" "F:\Windows\Boot\EFI\bootmgfw.efi"

takeown /f "F:\Windows\System32\winload.efi" /a
icacls "F:\Windows\System32\winload.efi" /grant SYSTEM:F
copy /y "C:\Windows\Temp\bootsign\winload.efi" "F:\Windows\System32\winload.efi"
echo DONE

REM 3. Запланувати як SYSTEM:
powershell -Command "\$time = (Get-Date).AddSeconds(20).ToString('HH:mm'); schtasks /create /sc once /tn 'SignWin7Files' /tr 'C:\path\to\sign.cmd' /ru SYSTEM /rl HIGHEST /st \$time /f"

REM 4. Запустити:
schtasks /run /tn 'SignWin7Files'
```

#### 5.4 Перевірка підпису
```powershell
Get-AuthenticodeSignature "F:\Windows\Boot\EFI\bootmgfw.efi" | Format-List Status,StatusMessage,SignerCertificate
```

Після підписування нашим сертифікатом:
- `Status` може бути `UnknownError` — це нормально для самопідписаного сертифіката
- `SignerCertificate.Subject` має показувати наш `CN=Windows 7 UEFI SecureBoot`
- Розмір файлу трохи зміниться (напр. 737KB → 732KB)

**Також експортувати свіжий .cer з LocalMachine** (той, яким реально підписали):
```powershell
$cert = Get-ChildItem -Path Cert:\LocalMachine\My -CodeSigningCert | Where-Object { $_.Subject -like '*Windows 7*' } | Select-Object -First 1
Export-Certificate -Cert $cert -FilePath "$env:USERPROFILE\Desktop\Win7BootCert2.cer" -Type CERT
```

### 6. Enroll сертифіката в UEFI Secure Boot

#### 6.1 Підготовка
- Скопіювати `Win7BootCert.cer` (або `Win7BootCert2.cer`) на **FAT32 USB** флешку
- BIOS НЕ читає NTFS

#### 6.2 Для MSI Z370-A PRO (і більшості MSI)

Увійти в BIOS (F2/Del при старті):

```
Settings → Security → Secure Boot → Key Management
```

**Стандартна процедура:**
1. `Provision Factory Default keys` → `[Disabled]` (перемикає в Custom Mode)
2. Якщо ключі стали `No Key` — ти в Setup Mode ✅
3. Вибрати `> Authorized Signatures` → Enter (розгорнути)
4. Має з'явитись `Add New Signature` або `Enroll Signature`
5. Вибрати → `From File` → знайти `.cer` файл на флешці
6. Підтвердити → Save
7. F10 → Save & Exit

**Якщо ключі НЕ стали `No Key` на кроці 2:**
- Вибрати `Save all Secure Boot variables` → Enter → Yes (скидає в Setup Mode)
- Повторити з кроку 3

**Якщо `Set New Var Aborted`:**
- Спробувати файл `.der` замість `.cer`
- Переконатись що USB флешка FAT32
- Переконатись що `Provision Factory Default keys = Disabled`
- Якщо нічого не допомагає: `Enroll all Factory Default keys` (повертає стандартні MS ключі) → знову `Provision Factory Default keys = Disabled` → повторити

### 7. Верифікація
- При старті має з'явитись меню: Windows 11 (default, 30s) та Windows 7
- Secure Boot має бути Active (перевірити в BIOS або `msinfo32.exe` в Windows)
- Windows 7 має завантажуватись без помилки 0xc0000428

**Якщо Windows 7 не стартує з Secure Boot:** ввімкнути CSM (Boot Mode → UEFI+Legacy) — Secure Boot при цьому вимкнеться, але обидві системи працюватимуть.

## Типові помилки

| Помилка | Причина | Рішення |
|---|---|---|
| `Failure when attempting to copy boot files` | Немає адмін-прав | Запустити через `Start-Process -Verb RunAs` |
| `0xc0000428` — недійсний підпис | Secure Boot блокує файли | Перепідписати (крок 5) або ввімкнути CSM |
| Чорний екран після вибору Win7 | Відеодрайвер UEFI GOP | Увімкнути CSM в BIOS або під'єднати до iGPU |
| Немає пункту Win7 в меню | BCD на іншому ESP | Зміна BIOS могла змінити активний ESP. Перевірити `mountvol S: /s` |
| `Set New Var Aborted` в BIOS | Не в Custom/Setup Mode | `Provision Factory Default keys → Disabled`, а потім `Save all Secure Boot variables` |
| `Get-AuthenticodeSignature` → `UnknownError` | Нормально для self-signed | У Secure Boot буде прийнято, якщо сертифікат в db |
| SYSTEM не знаходить сертифікат | Cert в CurrentUser, а не LocalMachine | Імпортувати PFX в `Cert:\LocalMachine\My` або створити там |

### 8. Відновлення оригінальних MS-підписаних файлів

Якщо кастомний підпис не працює (0xc0000428) — повернути оригінальні файли, підписані Microsoft.

**Якщо є .bak:**
```cmd
copy "F:\Windows\Boot\EFI\bootmgfw.efi.bak" "F:\Windows\Boot\EFI\bootmgfw.efi"
copy "F:\Windows\System32\winload.efi.bak" "F:\Windows\System32\winload.efi"
```

**Якщо .bak немає — взяти з ESP іншого диска (якщо Windows 7 має свій ESP):**
```cmd
REM змонтувати ESP диска Windows 7
diskpart /c "select disk 2 & select partition 3 & assign letter=X"
REM скопіювати bootmgfw.efi (оригінальний MS-підписаний)
copy "X:\EFI\Microsoft\Boot\bootmgfw.efi" "F:\Windows\Boot\EFI\bootmgfw.efi"
```

**Після відновлення обов'язково видалити кастомний сертифікат з UEFI db.**
В BIOS: `Key Management → Provision Factory Default keys → Enabled → Enroll all Factory Default keys`

### 9. Fallback: Dual Boot через CSM (без Secure Boot)

Найнадійніший спосіб для Windows 7 + Windows 11 dual boot:

**BIOS налаштування (MSI Z370-A PRO):**
```
Settings → Boot → CSM → Enabled
Boot mode filter → UEFI only  (Windows 11 через UEFI)
CSM → Boot from Storage → UEFI only
```

При CSM:
- Secure Boot автоматично вимикається (на MSI та більшості материнок)
- Windows 11 завантажується в UEFI режимі (нормально)
- Windows 7 завантажується через CSM (не потребує Secure Boot)
- Обидві системи працюють стабільно

**Якщо Win7 завантажується з чорним екраном при CSM:**
- У CSM: `Boot from Storage` → `Legacy only` (тільки для відеокарт без GOP)
- Або під'єднати монітор до вбудованої відеокарти (iGPU)

## Diagnostics

### Повний дамп дисків
```cmd
echo list disk | diskpart
```

### Детальна інформація
Створити скрипт `dscan.txt`:
```
select disk 0
detail disk
list partition
select disk 1
detail disk
list partition
```
Запустити: `diskpart /s dscan.txt`

### Перевірка активного ESP
```cmd
mountvol S: /s
dir S:\EFI\Microsoft\Boot
bcdedit /store S:\EFI\Microsoft\Boot\BCD /enum
```

### Перевірка підпису файлу
```powershell
Get-AuthenticodeSignature "F:\Windows\Boot\EFI\bootmgfw.efi" | Format-List Status,StatusMessage,SignerCertificate
```

## Бекап BCD
```cmd
bcdedit /export C:\bcd_backup.bcd
bcdedit /import C:\bcd_backup.bcd
```

## Додаткові матеріали
Див. `references/msi-secureboot-enrollment.md` — покрокова інструкція для MSI BIOS.
