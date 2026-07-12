# Hermes Windows Skills

> A curated collection of reusable Hermes Agent skills for Windows 10/11 desktop automation, computer-use optimization, and system administration.

**Document identifier:** HWS-001  
**Document status:** Release  
**Version:** 1.0.0  
**Date:** 2026-07-11  
**Classification:** Public  

---

## Table of Contents

1. [Scope](#1-scope)
2. [Normative References](#2-normative-references)
3. [Terms and Definitions](#3-terms-and-definitions)
4. [System Requirements](#4-system-requirements)
5. [Installation](#5-installation)
6. [Architecture](#6-architecture)
7. [Skill Inventory](#7-skill-inventory)
8. [Usage Guide](#8-usage-guide)
9. [Troubleshooting](#9-troubleshooting)
10. [Contributing](#10-contributing)
11. [License](#11-license)

---

## 1. Scope

This document specifies the **hermes-windows-skills** project — a collection of reusable skill modules for the [Hermes Agent](https://hermes-agent.nousresearch.com) framework. The skills address Windows-specific challenges encountered during desktop automation via the `computer_use` tool, including:

- Multi-monitor configuration and coordinate mapping
- Electron application window management
- Native Windows dialog interaction (Save As, file pickers)
- Chrome DevTools Protocol (CDP) integration
- PowerShell automation via git-bash environments
- MCP (Model Context Protocol) session management
- Antivirus and security software conflict resolution

### 1.1 Target Audience

- **Primary:** Hermes Agent users running on Windows 10 or Windows 11
- **Secondary:** AI agent developers integrating desktop automation on Windows
- **Tertiary:** System administrators deploying headless agent workflows on Windows

### 1.2 Intended Use

- Resolve known Windows-specific blockers in Hermes Agent desktop automation
- Provide battle-tested procedures for multi-monitor, Electron, and dialog interaction
- Serve as a reference implementation for community-contributed Windows skills

---

## 2. Normative References

| Reference | Title | Source |
|-----------|-------|--------|
| ISO/IEC 26514:2022 | Systems and software engineering — Requirements for designers and developers of user documentation | ISO |
| ISO/IEC 25010:2023 | Systems and software engineering — Quality model for software | ISO |
| Hermes Agent Docs | Hermes Agent User Guide and API Reference | [docs](https://hermes-agent.nousresearch.com/docs) |
| Hermes Agent Skills | Hermes Agent Skills Catalog | [skills](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| cua-driver | Hermes Agent computer-use driver specification | [cua-driver](https://github.com/NousResearch/hermes-agent) |

---

## 3. Terms and Definitions

| Term | Definition |
|------|------------|
| **Hermes Agent** | An open-source AI agent framework by Nous Research |
| **Skill** | A reusable Hermes Agent module (SKILL.md) containing procedural knowledge for a specific task domain |
| **computer_use** | A Hermes Agent tool that drives the desktop via cua-driver in background mode |
| **cua-driver** | The underlying binary that captures screenshots and simulates input on the desktop |
| **MCP** | Model Context Protocol — a standard for tool/server interaction |
| **SOM** | Set-of-Mark — numbered element overlays on screenshots for reliable clicking |
| **AX Tree** | Accessibility tree — structured representation of UI elements |
| **CDP** | Chrome DevTools Protocol — a protocol for automating Chromium browsers |
| **PostMessage** | Windows API mechanism for sending input events to background windows |
| **UIA** | UI Automation — Microsoft's accessibility framework |
| **Electron** | A framework for building desktop applications using web technologies |

---

## 4. System Requirements

### 4.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Operating System | Windows 10 22H2 | Windows 11 24H2 |
| RAM | 8 GB | 16 GB |
| Disk Space | 500 MB | 2 GB |
| Display | 1280 × 720 | 1920 × 1080 or higher |

### 4.2 Software Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Hermes Agent | ≥ 0.7.0 | Must support `computer_use` tool |
| cua-driver | ≥ 0.7.1 | Ships with Hermes Agent |
| PowerShell | ≥ 5.1 | Built into Windows |
| git-bash / MSYS2 | Any | For terminal tool compatibility |
| Chrome or Edge | Current | For CDP-based automation |

### 4.3 Hermes Agent Configuration

Ensure the following toolsets are enabled in Hermes Agent:

```bash
hermes tools enable computer_use
hermes tools enable terminal
hermes tools enable file
hermes tools enable web
```

---

## 5. Installation

### 5.1 Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/<your-org>/hermes-windows-skills.git
cd hermes-windows-skills

# Run the install script
bash scripts/install.sh
```

### 5.2 Manual Installation

```bash
# Copy skills to Hermes Agent skills directory
cp -r skills/* ~/.hermes/skills/

# Verify installation
hermes skills list | grep windows-computer-use
```

### 5.3 Install via Hermes Agent Skills Hub (Future)

```bash
# Once published to the skills hub
hermes skills install windows-computer-use
```

### 5.4 Post-Installation Verification

```bash
# Check that the skill is recognized
hermes skills list

# Load the skill in a session
hermes chat -s windows-computer-use -q "Show me the Windows multi-monitor setup guide"
```

---

## 6. Architecture

### 6.1 Repository Structure

```
hermes-windows-skills/
├── LICENSE                    # MIT License
├── README.md                  # This document
├── Makefile                   # Build and install automation
├── scripts/
│   ├── install.sh             # Automated installation
│   ├── verify.sh              # Post-installation verification
│   └── uninstall.sh           # Removal script
├── skills/
│   ├── windows-computer-use/  # Windows desktop automation skill
│   │   ├── SKILL.md           # Main skill document
│   │   └── references/        # Supplementary reference files
│   ├── software-development/  # Dev tools category
│   │   └── documaster/        # Doc generation & GitHub publishing
│   │       ├── SKILL.md
│   │       └── references/
│   └── ...                    # Additional skills (future)
├── docs/
│   ├── user-guide/            # End-user documentation
│   ├── developer-guide/       # Contributor documentation
│   ├── api/                   # API reference
│   └── references/            # External references
├── examples/
│   ├── multi-monitor/         # Multi-monitor configuration examples
│   ├── electron/              # Electron window management
│   └── cdp/                   # Chrome DevTools Protocol examples
└── .github/
    ├── ISSUE_TEMPLATE/        # Issue report templates
    └── workflows/             # CI/CD workflows
```

### 6.2 Skill Lifecycle

```
Installation → Session Load → Query → Agent Uses Skill → Feedback → Update
```

Each skill is a self-contained `SKILL.md` file with standardized frontmatter that Hermes Agent loads at session start. Skills can reference supporting files in `references/`, `scripts/`, and `templates/` subdirectories.

---

## 7. Skill Inventory

### 7.1 Current Skills

| Skill ID | Version | Description | Dependencies |
|----------|---------|-------------|--------------|
| `windows-computer-use` | 1.1.0 | Windows-specific computer_use patterns: multi-monitor, Electron, CDP, MCP | Hermes Agent ≥ 0.7.0 |
| `windows-computer-use-stable` | 1.0.0 | Fallback automation via MCP + mss/pyautogui + CDP/Selenium when cua-driver fails | Hermes Agent, Python |
| `windows-app-launcher` | 1.0.0 | Launch, maximize, and manage Windows applications via PowerShell, Win32 API, CDP | Hermes Agent |
| `windows-navigation-master` | 1.0.0 | Quick-reference Windows 11 navigation — files, apps, browser tabs, bookmarks | Hermes Agent |
| `windows-automation-enhanced` | 1.0.0 | Low-level Windows automation beyond computer_use: SendMessage, Win32 API, UI Automation | Python, pywin32 |
| `windows-diagnostics` | 1.0.0 | Windows 11 system diagnostics via PowerShell and Sysinternals | PowerShell ≥ 5.1 |
| `windows-chrome-automation` | 1.0.0 | Fast Chrome + Windows 11 automation via Win32 API + CDP | Chrome, Python |
| `windows-system-administration` | 1.0.0 | Comprehensive Windows system administration & security hardening | Administrator |
| `windows-wsl-python-setup` | 1.0.0 | Python project setup from GitHub on Windows/WSL | WSL, Python |
| `windows-remote-access-setup` | 1.0.0 | Setup remote access via AnyDesk, RustDesk, Tailscale SSH | Network |
| `windows-remote-access-tailscale-ssh` | 1.0.0 | Remote access via Tailscale SSH — no password, no open ports | Tailscale |
| `windows-wsl2-conversion-and-autostart` | 1.0.0 | Windows → WSL 2 conversion + Hyper-V enable + WSL autostart | Windows Pro |
| `windows7-uefi-secureboot` | 1.0.0 | Add Windows 7 to BCD for Dual Boot with UEFI SecureBoot | Windows 11 |
| `documaster` | 1.0.0 | Automated technical documentation generation and GitHub publishing via PR | PyGithub, GITHUB_TOKEN |

### 7.2 Planned Skills

| Skill ID | Priority | Status |
|----------|----------|--------|

---

## 8. Usage Guide

### 8.1 Loading a Skill in Hermes Agent

**From the command line:**

```bash
hermes chat -s windows-computer-use
```

**From within a session:**

```
/skill windows-computer-use
```

**In a cron job:**

```yaml
skills:
  - windows-computer-use
prompt: "Check monitor configuration and report..."
```

### 8.2 Skill Directory

After installation, skills are available at:

```
~/.hermes/skills/<category>/<skill-name>/SKILL.md
```

For this collection:

```
~/.hermes/skills/windows-computer-use/SKILL.md
```

### 8.3 Deploying to Multiple Hermes Profiles

```bash
# Install to a specific profile
cp -r skills/* ~/.hermes/profiles/<profile-name>/skills/
```

---

## 9. Troubleshooting

### 9.1 Skill Not Loading

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `skill not found` | Skill not installed | Run `scripts/install.sh` |
| `invalid frontmatter` | Malformed SKILL.md | Validate with `scripts/verify.sh` |
| `description too long` | Exceeds 1024 chars | Edit SKILL.md description field |

### 9.2 Computer Use Issues

Refer to the in-skill troubleshooting section (`skill_view(name="windows-computer-use")`) or see `docs/user-guide/troubleshooting.md`.

### 9.3 Reporting Issues

File an issue at the GitHub repository using the provided issue templates.

---

## 10. Contributing

Contributions are welcome! Please see:

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Contribution guidelines
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — Code of conduct
- [`docs/developer-guide/`](docs/developer-guide/) — Developer documentation

### 10.1 Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/<your-org>/hermes-windows-skills.git
cd hermes-windows-skills

# Create a branch
git checkout -b feat/my-new-skill

# Validate your skill
bash scripts/verify.sh skills/my-skill/SKILL.md

# Submit a pull request
```

---

## 11. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Document History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-07-11 | Hermes Windows Skills Contributors | Initial release |
