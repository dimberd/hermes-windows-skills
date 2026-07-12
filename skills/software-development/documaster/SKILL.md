---
name: documaster
description: >-
  Use when you need to analyze source code, generate professional technical
  documentation in Markdown (ISO/IEC 26514:2022), and publish it to a GitHub
  repository via the GitHub API (branch, commit, pull request).
version: 1.0.0
author: Hermes Agent Community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documentation, github, devops, technical-writing, iso-26514]
    related_skills: [github-pr-workflow, github-repo-management]
---

# DocuMaster

> Automated technical documentation generation and GitHub publishing.

## Overview

DocuMaster analyzes source code repositories and generates professional
technical documentation following ISO/IEC 26514:2022 standards. It then
publishes the documentation to GitHub by creating a dedicated branch,
committing the documentation files, and opening a pull request.

This skill is designed for developers, DevOps engineers, and technical
writers who need to maintain up-to-date documentation without manual
effort.

## When to Use

- A new project or feature needs initial documentation
- Documentation is outdated and needs a refresh
- You need a standardized documentation structure following ISO norms
- You want to publish documentation as a GitHub pull request automatically
- You need to document a public API, CLI tool, or library

**Do NOT use when:**
- The repository is not hosted on GitHub
- You don't have `GITHUB_TOKEN` available
- The task requires interactive documentation review before publishing
  (use `plan` skill instead for draft mode)

## Prerequisites

| Requirement | Details |
|-------------|---------|
| GitHub Token | `GITHUB_TOKEN` env var with `repo` scope |
| Python | ≥ 3.8 (for PyGithub when used via scripts) |
| Network | HTTPS access to `api.github.com` |
| Target Repo | Must exist and be accessible by the token |

## Algorithm

### Phase 1: Context Analysis

1. **Scan project structure**
   ```bash
   find . -type f -not -path './.git/*' -not -path './node_modules/*' \
          -not -path './__pycache__/*' | head -80
   ```

2. **Identify key files**
   - `package.json` / `requirements.txt` / `pyproject.toml` / `Cargo.toml`
   - Main entry point (e.g. `main.py`, `index.js`, `src/lib.rs`)
   - Configuration files (`.env.example`, `config.yaml`, `docker-compose.yml`)
   - Test files and CI configuration

3. **Extract public API**
   - Function/method signatures with docstrings
   - CLI commands and flags (look for argparse, click, typer)
   - Environment variables the application reads
   - Exported classes, types, and interfaces

4. **Determine project purpose**
   - Read `README.md` if it exists (may be outdated)
   - Read the main module docstring
   - Identify the build/test/run commands

### Phase 2: Documentation Generation

Generate a `README.md` or files under `docs/` following this structure:

```markdown
# Project Name

> One-line elevator pitch describing what this project does.

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Prerequisites](#3-prerequisites)
4. [Installation](#4-installation)
5. [Configuration](#5-configuration)
6. [Usage](#6-usage)
7. [API Reference](#7-api-reference)
8. [Development](#8-development)
9. [Troubleshooting](#9-troubleshooting)
10. [License](#10-license)
```

| Section | Content Requirements |
|---------|---------------------|
| **Overview** | 2-3 paragraphs: what, why, who it's for |
| **Features** | Bulleted list of key capabilities |
| **Prerequisites** | Hardware, software, accounts, tokens |
| **Installation** | **Step-by-step commands** — most important section. Include `git clone`, package manager, venv setup, verification |
| **Configuration** | Table of environment variables: `\| Variable \| Required \| Default \| Description \|` |
| **Usage** | Code examples for every major function/command. Include expected output |
| **API Reference** | Function signatures, parameters, return types |
| **Development** | How to run tests, lint, build, contribute |
| **Troubleshooting** | Common errors and their resolutions |

**Tone:** Professional, technical, concise. No vague phrases.
**Format:** ISO/IEC 26514:2022 compliant — clear document identification,
version history, normative references.

### Phase 3: GitHub Publishing

When `GITHUB_TOKEN` is available and the user confirms:

1. **Get current repository state**
   ```python
   from github import Github
   g = Github(GITHUB_TOKEN)
   repo = g.get_repo("owner/repo")
   contents = repo.get_contents("")
   ```

2. **Create a new branch**
   ```python
   branch_name = f"docs/update-documentation-{int(time.time())}"
   source_branch = repo.get_branch("main")
   repo.create_git_ref(
       ref=f"refs/heads/{branch_name}",
       sha=source_branch.commit.sha
   )
   ```

3. **Write documentation files**
   ```python
   repo.create_file(
       path="README.md",
       message="docs: update documentation via DocuMaster",
       content=documentation_content,
       branch=branch_name
   )
   ```

4. **Create pull request**
   ```python
   repo.create_pull(
       title="docs: update project documentation",
       body="""## Summary

   Automated documentation update generated by DocuMaster.

   ### Changes
   - Updated README.md with ISO/IEC 26514:2022 compliant structure
   - Added installation, configuration, usage, and troubleshooting sections

   ### Review Checklist
   - [ ] Installation steps are accurate
   - [ ] Environment variables documented
   - [ ] Code examples are tested
   - [ ] API reference is complete
   """,
       head=branch_name,
       base="main"
   )
   ```

## Completion Criteria

- [ ] Project structure scanned and documented
- [ ] All key dependencies and their purposes identified
- [ ] README.md generated with ISO-compliant structure
- [ ] Installation steps are complete and verifiable
- [ ] Environment variables documented in table format
- [ ] Code examples exist for every public API function
- [ ] GitHub branch created and documentation committed
- [ ] Pull request opened with descriptive summary
- [ ] User notified with PR URL

## Common Pitfalls

1. **Missing GITHUB_TOKEN** — The most common failure. Check: `echo $GITHUB_TOKEN`. If empty, ask the user to set it or provide a token.

2. **Wrong token scope** — Token needs at least `repo` scope for private repos. Verify: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`.

3. **Repository not found** — The repo must already exist. Create it first via `gh repo create` or GitHub web UI.

4. **Stale documentation overwrite** — Always read the existing README.md before overwriting. Merge valuable existing content rather than replacing it.

5. **Empty PR body** — Always include a meaningful PR description so reviewers understand what changed.

6. **No PyGithub installed** — Run `pip install PyGithub` before Phase 3. If not available, use raw `curl` with GitHub REST API as fallback:

   ```bash
   # Create branch via REST API
   curl -s -X POST \
     -H "Authorization: token $GITHUB_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ref":"refs/heads/new-branch","sha":"COMMIT_SHA"}' \
     https://api.github.com/repos/owner/repo/git/refs
   ```

7. **Rate limiting** — Unauthenticated requests are limited to 60/hour. Authenticated: 5000/hour. If you hit the limit, the token may be missing or invalid.

8. **Binary/large files** — Don't include compiled binaries, archives, or dependency lockfiles in documentation. Focus on source code and configuration.

## Scripts

A helper script for Phase 3 GitHub operations can be found at:

```
references/github-publish.py
```

Usage:
```bash
python references/github-publish.py --token $GITHUB_TOKEN --repo owner/repo \
  --branch "docs/update" --file README.md --content "$(cat README.md)"
```

## Verification Checklist

- [ ] Project scanned: files, dependencies, API surface
- [ ] README.md: Title, Description, Installation (step-by-step), Usage (examples), Configuration (env table)
- [ ] Installation steps actually work (test by following them literally)
- [ ] Environment variables documented with `| Variable | Required | Default | Description |` table
- [ ] PR created with `docs:` prefix in title
- [ ] PR body includes summary, changes list, and review checklist
- [ ] User has been shown the PR URL
