# Contributing Workflow

## Branch Naming

```
feat/<skill-name>      — New skill
fix/<skill-name>       — Bug fix
docs/<topic>           — Documentation
refactor/<skill-name>  — Refactoring
chore/<topic>          — Maintenance
```

## Commit Messages

```
<type>: <concise description>

Optional body explaining motivation.
```

Types: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`

Examples:
```
feat: add windows-computer-use skill for multi-monitor automation
fix: correct PowerShell $_ escaping in git-bash examples
docs: add troubleshooting section for Save As dialog
```

## Pull Request Checklist

- [ ] Skill passes `bash scripts/verify.sh`
- [ ] README.md updated if adding new skill
- [ ] Examples created in `examples/` directory
- [ ] Frontmatter complete (name, description, version, author, license)
- [ ] No personal data, paths, or credentials
- [ ] Description ≤ 1024 chars and trigger-focused
- [ ] Skill loaded and tested in a Hermes session
- [ ] License file updated if adding third-party code

## Review Process

1. Automated checks run via GitHub Actions
2. At least one maintainer reviews the code
3. Feedback addressed within 14 days
4. Squash merge on approval

## Adding a New Skill

```bash
# Create skill directory
mkdir -p skills/<category>/<skill-name>/{references,scripts,templates}

# Write SKILL.md
# ... (see skill-authoring.md for format)

# Validate
bash scripts/verify.sh skills/<category>/<skill-name>/SKILL.md

# Add examples
mkdir -p examples/<skill-name>
# ... create example files

# Commit
git add skills/<category>/<skill-name>/
git commit -m "feat: add <skill-name> skill"
```
