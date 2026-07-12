# ============================================================
#  DENISBOSS DIAGNOSTIC — все в одному
#  Виконує комплексну діагностику системи
# ============================================================

$outFile = "$env:TEMP\denisboss_diag_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
function Log($m) { Add-Content -Path $outFile -Value $m; Write-Host $m }

Log "============================================="
Log "ДІАГНОСТИКА DENISBOSS — $(Get-Date)"
Log "============================================="

# ---- 1. СИСТЕМНА ІНФОРМАЦІЯ ----
Log "`n=== 1. СИСТЕМА ==="
$os = Get-CimInstance Win32_OperatingSystem
Log "OS: $($os.Caption) $($os.Version)"
Log "Boot: $($os.LastBootUpTime)"
$uptime = (Get-Date) - $os.LastBootUpTime
Log "Uptime: $($uptime.Days)д $($uptime.Hours)год $($uptime.Minutes)хв"
$cpu = Get-CimInstance Win32_Processor
Log "CPU: $($cpu.Name) ($($cpu.NumberOfCores) ядер)"
$ram_gb = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$ram_free = [math]::Round($os.FreePhysicalMemory/1MB, 1)
Log "RAM: $ram_free GB free / $ram_gb GB total ($([math]::Round($ram_free/$ram_gb*100,1))% free)"

# ---- 2. КРИТИЧНІ ВИМКНЕННЯ (Kernel-Power 41) ----
Log "`n=== 2. КРИТИЧНІ ВИМКНЕННЯ ==="
$cp = Get-WinEvent -FilterHashtable @{LogName="System"; Id=41} -ErrorAction SilentlyContinue
$cp_count = if ($cp) { ($cp | Measure-Object).Count } else { 0 }
Log "Kernel-Power 41 (несподівані вимкнення): $cp_count разів"
if ($cp_count -gt 0) {
    $cp | Sort-Object TimeCreated -Descending | Select-Object -First 10 | ForEach-Object {
        Log "  $($_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))"
    }
}

# ---- 3. ВСІ КРИТИЧНІ ПОМИЛКИ SYSTEM LOG ----
Log "`n=== 3. КРИТИЧНІ ПОМИЛКИ SYSTEM (Level=1, останні 20) ==="
$crit = Get-WinEvent -FilterHashtable @{LogName="System"; Level=1} -MaxEvents 20 -ErrorAction SilentlyContinue
if ($crit) {
    $crit | ForEach-Object {
        $src = $_.ProviderName
        if ($src.Length -gt 60) { $src = $src.Substring(0,60) }
        Log "  $($_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')) | ID:$($_.Id) | $src"
    }
} else { Log "  (немає)" }

# ---- 4. BSOD / Windows Error Reporting ----
Log "`n=== 4. BSOD / WINDOWS ERROR REPORTING ==="
$wer = Get-WinEvent -FilterHashtable @{LogName="Application"; Id=1001} -MaxEvents 15 -ErrorAction SilentlyContinue
if ($wer) {
    $wer | ForEach-Object {
        $msg = $_.Message
        if ($msg -match "(.{0,100})") { $short = $matches[1] }
        Log "  $($_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))"
        Log "    $($msg.Substring(0, [Math]::Min(200, $msg.Length)))"
        Log "    ---"
    }
} else { Log "  (немає BSOD звітів)" }

# ---- 5. MINIDUMP ----
Log "`n=== 5. MINIDUMP ==="
$md = Get-ChildItem "C:\Windows\Minidump" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($md) {
    Log "Файлів minidump: $($md.Count)"
    $md | Select-Object -First 10 | ForEach-Object {
        Log "  $($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')) | $($_.Name) | $([math]::Round($_.Length/1KB,1)) KB"
    }
} else { Log "  Minidump: немає" }
$mem = Get-ChildItem "C:\Windows\MEMORY.DMP" -ErrorAction SilentlyContinue
if ($mem) {
    Log "  MEMORY.DMP: $($mem[0].LastWriteTime) — $([math]::Round($mem[0].Length/1MB,1)) MB"
} else { Log "  MEMORY.DMP: немає" }

# ---- 6. EVENT 1074 (чисті вимкнення/перезавантаження) ----
Log "`n=== 6. ПЕРЕЗАВАНТАЖЕННЯ (1074) за останні 7 днів ==="
$rbt = Get-WinEvent -FilterHashtable @{LogName="System"; Id=1074} -MaxEvents 30 -ErrorAction SilentlyContinue
if ($rbt) {
    $rbt | ForEach-Object {
        $msg = $_.Message
        $user = "?"
        if ($msg -match "on behalf of user (.+?) for") { $user = $matches[1] }
        $reason = "?"
        if ($msg -match "for the following reason: (.+?)$") { $reason = $matches[1].Trim() }
        Log "  $($_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')) | user: $user | reason: $reason"
    }
} else { Log "  (немає)" }

# ---- 7. WHEA (апаратні помилки) ----
Log "`n=== 7. WHEA (апаратні помилки) ==="
$whea = Get-WinEvent -FilterHashtable @{LogName="System"; ProviderName="Microsoft-Windows-WHEA-Logger"} -MaxEvents 10 -ErrorAction SilentlyContinue
if ($whea) { $whea | % { Log "  $($_.TimeCreated) ID:$($_.Id) — $($_.Message.Substring(0,[Math]::Min(150,$_.Message.Length)))" }
} else { Log "  (немає WHEA помилок)" }

# ---- 8. ПОМИЛКИ ДИСКІВ ----
Log "`n=== 8. ПОМИЛКИ ДИСКІВ ==="
$disk_err = Get-WinEvent -FilterHashtable @{LogName="System"; Id=7,11,153,134} -MaxEvents 15 -ErrorAction SilentlyContinue
if ($disk_err) {
    $disk_err | % { Log "  $($_.TimeCreated) ID:$($_.Id) — $($_.Message.Substring(0,[Math]::Min(200,$_.Message.Length)))" }
} else { Log "  (немає помилок дисків)" }

# ---- 9. S.M.A.R.T. СТАН ДИСКІВ ----
Log "`n=== 9. S.M.A.R.T. СТАН ДИСКІВ ==="
$disks = Get-PhysicalDisk -ErrorAction SilentlyContinue
if ($disks) {
    $disks | ForEach-Object {
        $health = $_.HealthStatus
        $opStatus = $_.OperationalStatus
        $size_gb = [math]::Round($_.Size/1GB, 1)
        Log "  $($_.FriendlyName) | $($_.MediaType) | $size_gb GB | Health: $health | Status: $opStatus"
    }
} else { Log "  (не вдалось отримати S.M.A.R.T.)" }

# ---- 10. ДИСКИ (ЛОГІЧНІ) ----
Log "`n=== 10. ДИСКИ (логічні томи) ==="
$vols = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"
$vols | ForEach-Object {
    $free_pct = [math]::Round($_.FreeSpace/$_.Size*100,1)
    $size_gb = [math]::Round($_.Size/1GB, 1)
    $free_gb = [math]::Round($_.FreeSpace/1GB, 1)
    Log "  $($_.DeviceID) | $size_gb GB | $free_gb GB free ($free_pct%)"
}

# ---- 11. МЕРЕЖЕВІ З'ЄДНАННЯ ----
Log "`n=== 11. МЕРЕЖЕВІ З'ЄДНАННЯ (ESTABLISHED, зовнішні) ==="
$netstat_output = netstat -ano | Select-String "ESTABLISHED" | Select-String -NotMatch "127.0.0.1|192.168|100\.1[0-9][0-9]"
$netstat_output | ForEach-Object { Log "  $_" }

# ---- 12. СТАН SSH СЕРВІСУ ----
Log "`n=== 12. SSH СЕРВІС ==="
$svc = Get-Service -Name sshd -ErrorAction SilentlyContinue
if ($svc) { Log "  sshd: $($svc.Status) | Start: $($svc.StartType)" } else { Log "  sshd: не встановлено" }

# ---- 13. WINDOWS UPDATE СТАТУС ----
Log "`n=== 13. WINDOWS UPDATE ==="
try {
    $updateSession = New-Object -ComObject Microsoft.Update.Session
    $updateSearcher = $updateSession.CreateUpdateSearcher()
    $historyCount = $updateSearcher.GetTotalHistoryCount()
    Log "  Історія оновлень: $historyCount записів"
    $history = $updateSearcher.QueryHistory(0, [Math]::Min(10, $historyCount))
    $history | ForEach-Object {
        $date = if ($_.Date) { $_.Date.ToString("yyyy-MM-dd") } else { "?" }
        Log "  $date | $($_.Title.Substring(0, [Math]::Min(80, $_.Title.Length))) | $($_.ResultCode)"
    }
} catch { Log "  (не вдалось отримати — можливо служба вимкнена)" }

# ---- 14. РЕСУРСИ (CPU, RAM, диск) ----
Log "`n=== 14. ПОТОЧНЕ НАВАНТАЖЕННЯ ==="
$cpu_load = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
Log "  CPU: $cpu_load%"
$proc_top = Get-Process | Sort-Object CPU -Descending | Select-Object -First 5
$proc_top | % { Log "  $($_.ProcessName) | CPU: $([math]::Round($_.CPU,1))s | RAM: $([math]::Round($_.WorkingSet64/1MB,1)) MB" }

# ---- 15. CHKDSK СТАТУС (чи очікує перевірка при завантаженні) ----
Log "`n=== 15. CHKDSK СТАТУС ==="
$chkdsk_flag = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -Name "BootExecute" -ErrorAction SilentlyContinue
if ($chkdsk_flag -and $chkdsk_flag.BootExecute -join " " -match "chkdsk|autochk") {
    Log "  ⚠️ CHKDSK заплановано при наступному завантаженні: $($chkdsk_flag.BootExecute -join ' ')"
} else {
    Log "  ✅ CHKDSK не заплановано"
}

# ---- 16. ДОДАТКОВО: Reliability Monitor події ----
Log "`n=== 16. RELIABILITY MONITOR (Microsoft-Windows-Diagnostics-Performance) ==="
$rel = Get-WinEvent -FilterHashtable @{LogName="Microsoft-Windows-Diagnostics-Performance/Operational"; Id=100,101,200,201} -MaxEvents 15 -ErrorAction SilentlyContinue
if ($rel) {
    $rel | ForEach-Object {
        Log "  $($_.TimeCreated) ID:$($_.Id) — $($_.LevelDisplayName) | $($_.ProviderName)"
    }
} else { Log "  (не доступно або немає подій)" }

# ---- 17. АПАРАТНА ІНФОРМАЦІЯ ----
Log "`n=== 17. АПАРАТУРА ==="
$bios = Get-CimInstance Win32_BIOS
Log "  BIOS: $($bios.Manufacturer) $($bios.Name)"
$mb = Get-CimInstance Win32_BaseBoard
Log "  Motherboard: $($mb.Manufacturer) $($mb.Product)"
$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1
if ($gpu) { Log "  GPU: $($gpu.Name) | RAM: $([math]::Round($gpu.AdapterRAM/1GB,1)) GB" }

# ---- ПІДСУМОК ----
Log "`n============================================="
Log "ДІАГНОСТИКА ЗАВЕРШЕНА"
Log "Файл збережено: $outFile"
Log "============================================="

# Вивести шлях до файлу
Write-Host "`nOUTPUT_FILE:$outFile"
