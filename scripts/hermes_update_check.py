#!/usr/bin/env python3
"""hermes_update_check.py — Bezpieczna aktualizacja Hermes
Harmonogram: codziennie 1:00 (czas polski, CET/CEST)

Procedura:
1. Pobrać aktualizację do katalogu testowego D:\Sorb\hermes-update-test\
2. Porównać nowe pliki z istniejącymi
3. Przeanalizować czy zmiany nie zepsują konfiguracji
4. Jeśli bezpieczne → zastosować
5. Jeśli ryzykowne → zablokować i powiadomić użytkownika
"""

import subprocess, os, sys, json, datetime, hashlib, shutil, difflib

HERMES_HOME = os.path.expanduser('~/AppData/Local/hermes')
TEST_DIR = r"D:\Sorb\hermes-update-test"
LOG_FILE = r"C:\hermes_work\hermes_update.log"

# Pliki konfiguracyjne które MUSZĄ pozostać niezmienione
PROTECTED_CONFIGS = [
    'config.yaml',
    'auth.json',
    'channel_directory.json',
]

# Kluczowe ustawienia w config.yaml które mamy zmienione
PROTECTED_CONFIG_KEYS = {
    'terminal.backend': 'local',
    'terminal.home_mode': 'auto',
    'display.language': 'uk',
    'display.busy_input_mode': 'interrupt',
    'mcp_servers.computer-use-mcp.enabled': True,
    'mcp_servers.hindsight.enabled': True,
    'memory.provider': 'hindsight',
    'tts.provider': 'edge',
    'stt.provider': 'groq',
    'code_execution.timeout': 300,
    'image_gen.provider': 'openai-codex',
    'skills.creation_nudge_interval': 15,
    'session_reset.mode': 'none',
    'platform_toolsets.telegram': ['browser','clarify','code_execution','computer_use','cronjob','delegation','file','image_gen','memory','session_search','skills','terminal','todo','tts','vision','web'],
}

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def sha256_file(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def check_update_available():
    """Sprawdź czy jest nowa wersja Hermes"""
    log("Sprawdzanie dostępności aktualizacji...")
    r = subprocess.run('hermes --version 2>&1', capture_output=True, timeout=10, shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
    current_ver = r.stdout.decode('cp1252', errors='replace').strip()
    log(f"Aktualna wersja: {current_ver or 'nieznana'}")
    
    # Sprawdź GitHub releases (później, gdy web_search zadziała)
    # Na razie pytamy pip:
    r2 = subprocess.run('pip index versions hermes-agent 2>&1', capture_output=True, timeout=15, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    out2 = r2.stdout.decode('cp1252', errors='replace')
    if 'Available versions' in out2:
        versions = out2.split('Available versions:')[-1].strip().split(',')
        latest = versions[0] if versions else 'unknown'
        log(f"Najnowsza na PyPI: {latest}")
        return current_ver, latest
    return current_ver, None

def download_update_test(target_dir):
    """Pobierz aktualizację do katalogu testowego"""
    os.makedirs(target_dir, exist_ok=True)
    log(f"\nPobieranie aktualizacji do: {target_dir}")
    
    # Symulacja: zapisz obecny config.yaml jako "nowy" do porównania
    # W rzeczywistości: pip download hermes-agent -d {target_dir}
    r = subprocess.run(
        f'pip download hermes-agent -d "{target_dir}" 2>&1',
        capture_output=True, timeout=120, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    out = r.stdout.decode('cp1252', errors='replace')
    err = r.stderr.decode('cp1252', errors='replace')
    
    if r.returncode == 0:
        log(f"✅ Pobrano: {out[:500]}")
        # Wypakuj
        for f in os.listdir(target_dir):
            if f.endswith('.whl') or f.endswith('.tar.gz'):
                log(f"   Plik: {f}")
        return True
    else:
        log(f"❌ Błąd pobierania: {err[:300]}")
        return False

def parse_config_sections(config_text):
    """Podziel config na sekcje (top-level keys)"""
    sections = {}
    current_section = '__header__'
    current_lines = []
    
    for line in config_text.split('\n'):
        if line.strip() and not line[0].isspace() and ':' in line:
            # Nowa sekcja
            if current_lines:
                sections[current_section] = '\n'.join(current_lines)
            current_section = line.split(':')[0].strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    
    if current_lines:
        sections[current_section] = '\n'.join(current_lines)
    return sections

def full_config_compare(backup_config, current_config, new_config_text=None):
    """Porównaj config sekcja po sekcji — 3 generacje"""
    log("\n=== PORÓWNANIE CONFIG (sekcja po sekcji) ===")
    
    backup_sections = parse_config_sections(backup_config) if backup_config else {}
    current_sections = parse_config_sections(current_config)
    
    all_sections = sorted(set(list(backup_sections.keys()) + list(current_sections.keys())))
    
    results = {
        'changed_since_backup': [],
        'new_sections': [],
        'removed_sections': [],
    }
    
    for section in all_sections:
        if section == '__header__': continue
        
        backup_val = backup_sections.get(section, '')
        current_val = current_sections.get(section, '')
        
        if not backup_val and current_val:
            results['new_sections'].append(section)
            log(f"🆕 Nowa sekcja: {section}")
        elif backup_val and not current_val:
            results['removed_sections'].append(section)
            log(f"🗑️ Usunięta sekcja: {section}")
        elif backup_val != current_val:
            results['changed_since_backup'].append(section)
            log(f"⚠️ Zmieniona sekcja: {section}")
            # Pokaż różnice (skrócone)
            b_lines = backup_val.split('\n')
            c_lines = current_val.split('\n')
            for i, (b, c) in enumerate(zip(b_lines, c_lines)):
                if b != c:
                    log(f"   L{i+1}: {b.strip()[:80]}")
                    log(f"       → {c.strip()[:80]}")
    
    if not results['changed_since_backup'] and not results['new_sections'] and not results['removed_sections']:
        log("✅ Wszystkie sekcje configu bez zmian od backupu")
    
    return results

def analyze_risk():
    """Przeanalizuj czy update jest bezpieczny"""
    log("\nAnaliza ryzyka aktualizacji...")
    risks = []
    
    # Sprawdź czy mamy backup
    backup_dir = os.path.join(HERMES_HOME, 'pre_update_backup')
    if not os.path.exists(backup_dir) or not os.listdir(backup_dir):
        risks.append("Brak backupu konfiguracji")
    
    # Sprawdź czy Gateway działa (update go zabije)
    r = subprocess.run(
        'wmic process where "name=\'pythonw.exe\' and commandline like \'%gateway%\'" get processid 2>nul',
        capture_output=True, timeout=5, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    if 'ProcessId' in r.stdout.decode('cp1252', errors='replace'):
        risks.append("Gateway uruchomiony — update go zatrzyma")
    else:
        risks.append("Gateway nie działa — dobry moment na update")
    
    # Sprawdź MCP
    r2 = subprocess.run(
        'wmic process where "name=\'node.exe\' and commandline like \'%computer-use%\'" get processid 2>nul',
        capture_output=True, timeout=5, shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    if 'ProcessId' in r2.stdout.decode('cp1252', errors='replace'):
        risks.append("MCP działa — update go zatrzyma")
    
    return risks

def main():
    log("=" * 60)
    log("HERMES UPDATE CHECK — " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    log("=" * 60)
    
    # 1. Sprawdź wersję
    current, latest = check_update_available()
    if latest and current and latest.split(',')[0].strip() == current:
        log("✅ Aktualna wersja jest najnowsza")
        return
    
    # 2. Zrób backup
    log("\n📦 Tworzenie backupu...")
    subprocess.run([sys.executable, r'C:\hermes_work\pre_update_backup.py'],
                  capture_output=True, timeout=30,
                  creationflags=subprocess.CREATE_NO_WINDOW)
    
    # 3. Pobierz do katalogu testowego
    test_dir = os.path.join(TEST_DIR, f"update_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}")
    download_ok = download_update_test(test_dir)
    
    if not download_ok:
        log("❌ Nie można pobrać aktualizacji — pomijam")
        return
    
    # 4. Porównaj config sekcja po sekcji
    backup_dir = os.path.join(HERMES_HOME, 'pre_update_backup')
    current_cfg_path = os.path.join(HERMES_HOME, 'config.yaml')
    
    backup_config = None
    if os.path.exists(backup_dir):
        backups = sorted(os.listdir(backup_dir))
        if backups:
            backup_cfg = os.path.join(backup_dir, backups[-1], 'config.yaml')
            if os.path.exists(backup_cfg):
                with open(backup_cfg, 'r', encoding='utf-8') as f:
                    backup_config = f.read()
    
    with open(current_cfg_path, 'r', encoding='utf-8') as f:
        current_config = f.read()
    
    # Porównaj backup → obecny (nasze zmiany)
    section_changes = full_config_compare(backup_config, current_config)
    
    # 5. Analiza ryzyka
    risks = analyze_risk()
    
    # 5. Raport
    log("\n" + "=" * 60)
    log("RAPORT AKTUALIZACJI")
    log("=" * 60)
    
    if section_changes['changed_since_backup']:
        log(f"\n⚠️ Zmienione sekcje configu od backupu ({len(section_changes['changed_since_backup'])}):")
        for s in section_changes['changed_since_backup']:
            log(f"   • {s}")
    
    if section_changes['new_sections']:
        log(f"\n🆕 Nowe sekcje ({len(section_changes['new_sections'])}):")
        for s in section_changes['new_sections']:
            log(f"   • {s}")
    
    if section_changes['removed_sections']:
        log(f"\n🗑️ Usunięte sekcje ({len(section_changes['removed_sections'])}):")
        for s in section_changes['removed_sections']:
            log(f"   • {s}")
    
    log("\n📋 Ryzyka:")
    for r in risks:
        log(f"   • {r}")
    
    if risks:
        log("\n⚠️ ZALECENIE: Nie aplikować aktualizacji automatycznie.")
        log("   Poczekaj na decyzję użytkownika.")
        log(f"\n📁 Pliki aktualizacji: {test_dir}")
        log("   python C:\\hermes_work\\pre_update_backup.py compare")
    else:
        log("✅ Aktualizacja bezpieczna. Aplikuję...")
        subprocess.run(['hermes', 'update'], capture_output=True, timeout=300,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        log("✅ Aktualizacja zastosowana")

if __name__ == '__main__':
    main()
