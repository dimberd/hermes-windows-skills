.PHONY: install verify uninstall help

help:
	@echo "Targets:"
	@echo "  make install   — Install skills to ~/.hermes/skills/"
	@echo "  make verify    — Validate all skill files"
	@echo "  make uninstall — Remove skills from ~/.hermes/skills/"
	@echo "  make clean     — Remove temporary files"
	@echo ""
	@echo "Configuration:"
	@echo "  SKILLS_DIR=$(SKILLS_DIR)"

SKILLS_DIR = $(HOME)/.hermes/skills
SRC_DIR = skills
SCRIPTS_DIR = scripts

install:
	@echo "Installing Hermes Windows Skills..."
	bash scripts/install.sh

verify:
	@echo "Validating skill files..."
	bash scripts/verify.sh

uninstall:
	@echo "Removing Hermes Windows Skills..."
	bash scripts/uninstall.sh

clean:
	@find . -type f -name "*.bak" -delete
	@find . -type f -name "*.tmp" -delete
	@echo "✅ Clean complete."
