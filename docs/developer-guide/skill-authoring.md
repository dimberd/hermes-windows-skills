# Skill Authoring Guide

## Overview

This document specifies the requirements for creating and maintaining skills in the hermes-windows-skills repository. All skills must conform to the Hermes Agent skill specification and ISO/IEC 26514:2022 documentation standards.

## Skill Structure

Every skill follows this structure:

```
skills/<category>/<skill-name>/
├── SKILL.md            # Main skill document (required)
├── references/         # Supplementary reference files (optional)
├── scripts/            # Executable scripts (optional)
└── templates/          # Configuration templates (optional)
```

## SKILL.md Format

### Frontmatter

The file must start with `---` as the first bytes (no leading whitespace) and contain valid YAML frontmatter:

```yaml
---
name: skill-name
description: Use when <trigger>. <one-line description of behavior>.
version: 1.0.0
author: Hermes Agent Community
license: MIT
platforms: [windows]
keywords: [windows, computer-use, desktop]
metadata:
  hermes:
    tags: [descriptive, tags]
    related_skills: [other-skill]
---
```

### Required Fields

| Field | Constraint |
|-------|-----------|
| `name` | ≤ 64 chars, lowercase with hyphens |
| `description` | ≤ 1024 chars |
| `version` | Semantic versioning |
| `author` | Name or organization |
| `license` | SPDX identifier (e.g., MIT) |

### Content Structure

```
# Title

## Overview
1-2 paragraphs: what the skill does and why.

## When to Use
- Bulleted trigger conditions
- Counter-indications

## [Topic Sections]
- Quick-reference tables
- Code blocks with exact commands
- Hermes-specific recipes

## Common Pitfalls
Numbered list of mistakes and fixes.

## Verification Checklist
- [ ] Checkbox list
```

### Quality Principles

1. **Trigger-focused descriptions** — describe when to load, not what to do
2. **Completion criteria** — each step must have a checkable completion condition
3. **Progressive disclosure** — branch-specific detail goes in linked files
4. **No no-op prose** — every sentence should change agent behavior

## Validation

Before submitting, validate:

```bash
bash scripts/verify.sh skills/<category>/<skill-name>/SKILL.md
```

The validator checks:
- File starts with `---`
- Valid YAML frontmatter
- Required fields present
- Description ≤ 1024 chars
- File size ≤ 100,000 chars
- Name ≤ 64 chars, correct format

## Reference Files

Place bulky or branch-specific content in `references/` and reference from SKILL.md:

```markdown
For detailed troubleshooting, see `references/troubleshooting-guide.md`.
```

## Versioning

- Major: Breaking changes to skill interface
- Minor: New sections or significant additions
- Patch: Bug fixes, clarifications, new pitfalls
