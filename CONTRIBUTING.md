# Contributing to Hermes Windows Skills

First off, thank you for considering contributing to this project.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/<your-org>/hermes-windows-skills/issues)
2. If not, create a new issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include:
   - Hermes Agent version (`hermes --version`)
   - Windows version (`winver`)
   - cua-driver version (`cua-driver config`)
   - Steps to reproduce
   - Expected vs actual behavior

### Suggesting Enhancements

1. Open a [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
2. Describe the problem and proposed solution
3. Include use cases and examples

### Adding a New Skill

1. Read `docs/developer-guide/skill-authoring.md`
2. Follow the [Hermes Agent Skill Authoring](https://hermes-agent.nousresearch.com/docs/reference/skill-authoring) standards
3. Create your skill under `skills/<category>/<name>/SKILL.md`
4. Validate: `bash scripts/verify.sh skills/<category>/<name>/SKILL.md`
5. Submit a pull request

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-change`
3. Make your changes
4. Run verification: `bash scripts/verify.sh`
5. Commit with clear message: `feat: add windows-computer-use skill`
6. Push and open a pull request
7. Ensure CI passes

## Commit Convention

```
<type>: <concise description>

Optional body.
```

Types: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`

## Style Guide

- Markdown: Follow `docs/developer-guide/markdown-style.md`
- Shell scripts: Bash, POSIX-compatible, error handling with `set -e`
- Skills: ISO/IEC 26514 documentation standards
