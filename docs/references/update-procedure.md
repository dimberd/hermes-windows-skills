# Hermes Update Procedure — Bezpieczna aktualizacja

## Automatyczny harmonogram: codziennie 1:00 (czas polski)

---

## Krok 1 — Sprawdzenie dostępności aktualizacji

O 1:00 cron `nightly-update-check` uruchamia `hermes_update_check.py`.

Skrypt sprawdza:
- Aktualna wersja: `hermes --version`
- Najnowsza wersja: PyPI `pip index versions hermes-agent`
- GitHub releases (jeśli dostępne)

**Jeśli wersja jest najnowsza** → koniec, brak akcji.
**Jeśli jest nowsza** → przejście do Kroku 2.

---

## Krok 2 — Backup przed aktualizacją

Automatycznie uruchamiany `pre_update_backup.py`:

```
Backup → C:\Users\PL_home\AppData\Local\hermes\pre_update_backup\backup_YYYYMMDD_HHMMSS\
```

**Backup obejmuje:**

| Plik | Po co? |
|------|--------|
| `config.yaml` | Wszystkie ustawienia Hermes |
| `auth.json` | Tokeny autoryzacji |
| `channel_directory.json` | Kanały Telegram/Discord |
| `gateway_state.json` | Stan Gateway |
| `processes.json` | Rejestr procesów |
| `skills/` | Wszystkie skille (windows-system-administration, windows-computer-use-stable, itd.) |
| `pip_packages.json` | Lista pakietów Python |

---

## Krok 3 — Pobranie aktualizacji do katalogu testowego

```
python C:\hermes_work\hermes_update_check.py
```

Pobiera paczkę do **oddzielnego katalogu** (NIE nadpisuje działających plików):

```
D:\Sorb\hermes-update-test\update_YYYYMMDD_HHMM\
├── hermes_agent-*.whl        # Nowa wersja
├── config.yaml (nowy)         # Default config z nowej wersji
└── diff_report.txt            # Porównanie plików
```

**Dlaczego D:\Sorb\hermes-update-test\?**
- Dysk D: ma więcej wolnego miejsca
- Osobny katalog = nie mieszamy z działającymi plikami
- Łatwo porównać "stare vs nowe"

---

## Krok 4 — Porównanie plików (compatibility check)

Skrypt porównuje **3 generacje** plików:

```
┌─────────────────────────────────────────────────────────────┐
│                     PORÓWNANIE 3 GENERACJI                   │
├─────────────────────────────────────────────────────────────┤
│  Generacja A: Backup sprzed updatu                          │
│    C:\...\pre_update_backup\backup_20260712_125150\         │
│    → config.yaml (ORIGINAL — przed zmianami)                │
├─────────────────────────────────────────────────────────────┤
│  Generacja B: Obecna konfiguracja (working)                 │
│    C:\...\hermes\config.yaml (AKTUALNY — z naszymi zmianami)│
├─────────────────────────────────────────────────────────────┤
│  Generacja C: Nowa wersja z PyPI                            │
│    D:\Sorb\hermes-update-test\update_20260713_010000\       │
│    → config.yaml (NOWY — factory default)                   │
└─────────────────────────────────────────────────────────────┘
```

**Sprawdzane różnice:**

| Co porównujemy | Metoda | Co robimy jeśli różne |
|----------------|--------|----------------------|
| `config.yaml` A vs B | `diff` | Pokazujemy nasze zmiany |
| `config.yaml` B vs C | `diff` | Sprawdzamy czy nowa wersja coś zmienia |
| Kluczowe ustawienia | `grep` dla 15+ kluczy | Ostrzegamy jeśli nowy config nadpisuje nasze zmiany |

**Chronione klucze konfiguracyjne (nie mogą być nadpisane przez update):**

| Klucz | Nasza wartość | Ważne bo... |
|-------|--------------|-------------|
| `terminal.backend` | local | Używamy lokalnego terminala |
| `terminal.home_mode` | auto | Automatyczny home mode |
| `display.language` | uk | Język ukraiński w UI |
| `display.busy_input_mode` | interrupt | Przerwanie przy busy |
| `mcp_servers.computer-use-mcp.enabled` | true | Widzenie ekranu |
| `mcp_servers.hindsight.enabled` | true | Pamięć długotrwała |
| `memory.provider` | hindsight | Pamięć przez Hindsight |
| `tts.provider` | edge | Syntezator mowy |
| `stt.provider` | groq | Rozpoznawanie mowy |
| `code_execution.timeout` | 300 | Długie skrypty Python |
| `image_gen.provider` | openai-codex | Generowanie obrazów |
| `session_reset.mode` | none | Nie resetować sesji |
| `skills.creation_nudge_interval` | 15 | Tworzenie skilli |

---

## Krok 5 — Analiza ryzyka

Skrypt sprawdza:

```
□ Czy backup istnieje?                    → ✅/❌
□ Czy Gateway działa?                     → ⚠️ update go zabije
□ Czy MCP działa?                         → ⚠️ update go zatrzyma
□ Czy config zmienił się od backupu?      → ⚠️ nasze zmiany zostaną
□ Czy nowy config nadpisuje nasze klucze? → ❌ blokada aktualizacji
```

**Wynik analizy:**

| Status | Znaczenie | Działanie |
|--------|-----------|-----------|
| ✅ Bezpieczny | Nowa wersja nie zmienia konfiguracji | Automatyczny update |
| ⚠️ Uwaga | Są zmiany, ale nie krytyczne | Pytanie użytkownika |
| ❌ Ryzykowny | Nowa wersja nadpisuje nasze ustawienia | BLOKADA — czekamy na decyzję |

---

## Krok 6 — Aplikacja lub blokada

**Jeśli bezpieczne (✅):**
1. `hermes update` — aplikuje nową wersję
2. Sprawdza czy Gateway wstał
3. Sprawdza czy MCP działa
4. Wysyła raport: "✅ Aktualizacja udana"

**Jeśli ryzykowne (❌):**
1. Wysyła raport: "⚠️ Aktualizacja zablokowana — konflikt configu"
2. Pokazuje różnice: `python C:\hermes_work\pre_update_backup.py compare`
3. Czeka na decyzję użytkownika:
   - "Zastosuj i przywróć moje ustawienia ręcznie"
   - "Pomiń tę aktualizację"
   - "Zastosuj z nowym configiem (stracę zmiany)"

---

## Diagram przepływu

```
Godzina 1:00 (cron)
    │
    ▼
Sprawdź wersję (hermes --version vs PyPI)
    │
    ├── Aktualna → KONIEC
    │
    └── Nowsza → Backup (pre_update_backup.py)
                    │
                    ▼
              Pobierz do D:\Sorb\hermes-update-test\
                    │
                    ▼
              Porównaj config: backup → obecny → nowy
                    │
                    ▼
              Analiza ryzyka (15 kluczy)
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     Bezpieczne   Uwaga      Ryzykowne
        │           │           │
        ▼           ▼           ▼
     Update     Pytanie      BLOKADA
     auto       użytkownika  + raport
```

---

## Ręczne wywołanie

```bash
# Tylko sprawdź
python C:\hermes_work\hermes_update_check.py

# Porównaj config z backupem
python C:\hermes_work\pre_update_backup.py compare

# Zrób backup ręcznie
python C:\hermes_work\pre_update_backup.py
```

---

## Pliki

| Plik | Lokalizacja | Kopia w projekcie |
|------|-------------|-------------------|
| `hermes_update_check.py` | `C:\hermes_work\` | `scripts\hermes_update_check.py` |
| `hermes_diag.py` | `C:\hermes_work\` | `scripts\hermes_diag.py` |
| `pre_update_backup.py` | `C:\hermes_work\` | `scripts\pre_update_backup.py` |
| `proc_watchdog.py` | `C:\hermes_work\` | `scripts\proc_watchdog.py` |

Katalog testowy aktualizacji: `D:\Sorb\hermes-update-test\`
