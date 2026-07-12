#!/usr/bin/env python3
"""pre_update_backup.py — бекап конфігів Hermes перед апдейтом
Запускати перед кожним hermes update.
Зберігає: config.yaml, skills, cron jobs, plugin config, gateway state.
Після апдейту: порівняти з бекапом, відновити змінені налаштування.
"""

import os, json, shutil, datetime
from pathlib import Path

HERMES_HOME = os.path.expanduser('~/AppData/Local/hermes')
BACKUP_DIR = os.path.join(HERMES_HOME, 'pre_update_backup')
SKILLS_DIR = os.path.expanduser('~/AppData/Local/hermes/skills')

def backup():
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'backup_{ts}')
    os.makedirs(backup_path, exist_ok=True)
    
    files_to_backup = [
        os.path.join(HERMES_HOME, 'config.yaml'),
        os.path.join(HERMES_HOME, 'auth.json'),
        os.path.join(HERMES_HOME, 'channel_directory.json'),
        os.path.join(HERMES_HOME, 'gateway_state.json'),
        os.path.join(HERMES_HOME, 'processes.json'),
    ]
    
    for f in files_to_backup:
        if os.path.exists(f):
            shutil.copy2(f, backup_path)
            print(f"✅ {os.path.basename(f)}")
    
    # Backup skills
    skills_backup = os.path.join(backup_path, 'skills')
    if os.path.exists(SKILLS_DIR):
        shutil.copytree(SKILLS_DIR, skills_backup, 
                        ignore=shutil.ignore_patterns('.usage.json', '__pycache__'),
                        dirs_exist_ok=True)
        print(f"✅ skills/")
    
    # Save list of installed packages/versions
    pip_list = os.popen('pip list --format=json 2>nul').read()
    if pip_list:
        with open(os.path.join(backup_path, 'pip_packages.json'), 'w', encoding='utf-8') as f:
            f.write(pip_list)
        print(f"✅ pip_packages.json")
    
    print(f"\n📂 Backup: {backup_path}")
    return backup_path

def compare(backup_path):
    """Порівняти поточні файли з бекапом"""
    print(f"\n=== Порівняння з бекапом: {backup_path} ===")
    
    current_config = os.path.join(HERMES_HOME, 'config.yaml')
    backup_config = os.path.join(backup_path, 'config.yaml')
    
    if os.path.exists(current_config) and os.path.exists(backup_config):
        import difflib
        with open(current_config, 'r', encoding='utf-8') as f:
            curr = f.readlines()
        with open(backup_config, 'r', encoding='utf-8') as f:
            back = f.readlines()
        
        diff = list(difflib.unified_diff(back, curr, fromfile='backup', tofile='current'))
        if diff:
            print("⚠️ Зміни в config.yaml:")
            for line in diff[:30]:
                print(f"  {line.rstrip()}")
        else:
            print("✅ config.yaml — без змін")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'compare':
        backups = sorted(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else []
        if backups:
            compare(os.path.join(BACKUP_DIR, backups[-1]))
        else:
            print("❌ Немає бекапів")
    else:
        backup()
