#!/usr/bin/env python3
"""full_backup.py — Pełny backup Hermes (ZIP, wersjonowany)
- ZAWSZE pełna kopia wszystkich plików
- ZIP compression (~10 MB zamiast 37 MB)
- Wersjonowanie: v1, v2, v3...
- Przechowuje ostatnie 15 backupów
- Historia w backup_index.json i CHANGELOG.md
"""

import shutil, os, datetime, subprocess, json, sys, zipfile

HERMES_HOME = os.path.expanduser('~/AppData/Local/hermes')
BACKUP_ROOT = r'D:\Sorb\backup'
INDEX_FILE = os.path.join(BACKUP_ROOT, 'backup_index.json')
MAX_BACKUPS = 10

def get_next_version():
    index = load_index()
    versions = [v['version'] for v in index.get('backups', [])]
    return max(versions, default=0) + 1

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    return {'backups': []}

def save_index(index):
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def backup():
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    version = get_next_version()
    zip_name = f'v{version}.zip'
    zip_path = os.path.join(BACKUP_ROOT, zip_name)
    
    print(f"📦 BACKUP v{version}")
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    
    files_added = 0
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        # 1. Config
        for f in ['config.yaml', 'auth.json', 'channel_directory.json', 'gateway_state.json', 'processes.json']:
            path = os.path.join(HERMES_HOME, f)
            if os.path.exists(path):
                z.write(path, f'config/{f}')
                files_added += 1
        
        # 2. Skills
        skills_src = os.path.join(HERMES_HOME, 'skills')
        if os.path.exists(skills_src):
            for root, dirs, files in os.walk(skills_src):
                for f in files:
                    if f.endswith(('.md', '.py', '.vbs', '.ps1', '.json', '.yaml')):
                        path = os.path.join(root, f)
                        rel = os.path.relpath(path, os.path.dirname(HERMES_HOME))
                        z.write(path, rel)
                        files_added += 1
        
        # 3. Cron
        cron_src = os.path.join(HERMES_HOME, 'cron')
        if os.path.exists(cron_src):
            for root, dirs, files in os.walk(cron_src):
                for f in files:
                    path = os.path.join(root, f)
                    rel = os.path.relpath(path, os.path.dirname(HERMES_HOME))
                    z.write(path, rel)
                    files_added += 1
        
        # 4. Hermes work scripts
        work_dir = r'C:\hermes_work'
        if os.path.exists(work_dir):
            for f in os.listdir(work_dir):
                if f.endswith(('.py', '.vbs', '.ps1', '.md', '.txt', '.json', '.log')):
                    path = os.path.join(work_dir, f)
                    z.write(path, f'hermes_work/{f}')
                    files_added += 1
        
        # 5. Projekt
        proj_dir = r'D:\Sorb\projekty\hermes-windows-skills'
        if os.path.exists(proj_dir):
            for root, dirs, files in os.walk(proj_dir):
                if '.git' in root.split(os.sep):
                    continue
                for f in files:
                    if not f.endswith(('.pyc', '.log')):
                        path = os.path.join(root, f)
                        rel = os.path.relpath(path, r'D:\Sorb')
                        z.write(path, rel)
                        files_added += 1
        
        # 6. Gateway
        gw_dir = os.path.join(HERMES_HOME, 'gateway-service')
        if os.path.exists(gw_dir):
            for f in os.listdir(gw_dir):
                path = os.path.join(gw_dir, f)
                z.write(path, f'gateway-service/{f}')
                files_added += 1
        
        # 7. Pip list
        r = subprocess.run('pip list --format=columns 2>&1', capture_output=True, timeout=15, shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
        z.writestr('pip_packages.txt', r.stdout.decode('cp1252', errors='replace'))
        files_added += 1
    
    zip_size = os.path.getsize(zip_path)
    
    # Manifest
    manifest = {
        'version': version,
        'date': ts,
        'size_kb': zip_size // 1024,
        'files': files_added,
        'zip': zip_name,
    }
    
    # Index
    index = load_index()
    index['backups'].append(manifest)
    
    # Cleanup old
    all_backups = sorted(index['backups'], key=lambda x: x['version'])
    removed = []
    while len(all_backups) > MAX_BACKUPS:
        old = all_backups.pop(0)
        old_zip = os.path.join(BACKUP_ROOT, old['zip'])
        if os.path.exists(old_zip):
            os.remove(old_zip)
            removed.append(old['version'])
    
    index['backups'] = all_backups
    index['total'] = len(all_backups)
    index['total_size_mb'] = sum(v['size_kb'] for v in all_backups) // 1024
    index['latest'] = version
    save_index(index)
    
    # Push to GitHub (може не спрацювати з sandbox — це ок, головне backup на D:)
    try:
        r = subprocess.run(
            f'git -C "{BACKUP_ROOT}" add -A 2>&1 && git -C "{BACKUP_ROOT}" commit --allow-empty -m "v{version}: backup {ts[:10]}" 2>&1 && git -C "{BACKUP_ROOT}" push 2>&1',
            capture_output=True, timeout=60, shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        out = r.stdout.decode('cp1252', errors='replace') + r.stderr.decode('cp1252', errors='replace')
        if 'Everything up-to-date' in out:
            print(f"   🌐 GitHub: актуально")
        elif 'master' in out or 'main' in out or 'push' in out:
            print(f"   🌐 GitHub: запушено ✅")
        else:
            err_lower = out.strip().lower()
            if 'permission' in err_lower or 'denied' in err_lower:
                print(f"   🌐 GitHub: пропущено (sandbox) — бекап на D: є ✅")
            else:
                print(f"   🌐 GitHub: {out.strip()[:100]}")
    except Exception as e:
        print(f"   🌐 GitHub: пропущено — {e}")
    
    # CHANGELOG
    changelog_path = os.path.join(BACKUP_ROOT, 'CHANGELOG.md')
    line = f"| v{version} | {ts[:10]} | {zip_size//1024} KB | {files_added} plików |\n"
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pos = content.index('\n', content.index('|---|')) + 1 if '|---|' in content else len(content)
        content = content[:pos] + line + content[pos:]
    else:
        content = f"# Hermes Backup Changelog\n\n| Version | Data | Rozmiar | Zawartość |\n|---------|------|---------|-----------|\n{line}"
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ v{version} — {zip_size//1024} KB, {files_added} plików")
    print(f"📊 Total: {index['total']} backupów, ~{index['total_size_mb']} MB")
    if removed:
        print(f"   🗑️ Usunięte stare: v{', '.join(map(str, removed))}")
    return version

def list_backups():
    index = load_index()
    print("\n📦 HISTORIA BACKUPÓW")
    print("=" * 60)
    print(f"{'#':>4} {'Data':14s} {'Rozmiar':>8} {'Pliki':>6}")
    print("-" * 60)
    for b in sorted(index.get('backups', []), key=lambda x: x['version'], reverse=True):
        print(f"  v{b['version']:>2}  {b['date'][:10]:14s} {b['size_kb']:>6} KB  {b.get('files', 0):>4}")
    print("=" * 60)
    total = index.get('total_size_mb', 0)
    print(f"📊 {index.get('total', 0)} backupów, ~{total} MB total")

if __name__ == '__main__':
    if '--list' in sys.argv:
        list_backups()
    else:
        backup()
