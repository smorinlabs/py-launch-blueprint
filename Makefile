# bash, not zsh: the bootstrap layer must work on stock Linux (devcontainers,
# CI runners, fresh VMs) where zsh is typically absent.
SHELL := /bin/bash

# Text colors
BLACK := \033[30m
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
GRAY := \033[90m

# Background colors
BG_BLACK := \033[40m
BG_RED := \033[41m
BG_GREEN := \033[42m
BG_YELLOW := \033[43m
BG_BLUE := \033[44m
BG_MAGENTA := \033[45m
BG_CYAN := \033[46m
BG_WHITE := \033[47m

# Text styles
BOLD := \033[1m
DIM := \033[2m
ITALIC := \033[3m
UNDERLINE := \033[4m

# Reset
NC := \033[0m

CHECK := $(GREEN)✓$(NC)
CROSS := $(RED)✗$(NC)
DASH := $(GRAY)-$(NC)

.PHONY: all bootstrap check hook-check install-uv install-just install-docker install-docker-force install-flox set-path help install-just-force install-uv-force

all: help

# Two-level setup. This Makefile is Level 1 ONLY — the bootstrap that
# installs the base toolchain (just + uv). Everything after that is
# Level 2: `just setup` (dev env sync, git hooks, hook toolchain).
# Do not add project tasks here; they belong in the Justfile.

# uv installs first so the just fallback below can rely on it. Primary just
# install (just.systems) resolves the latest release via the anonymous GitHub
# API, which 403s on rate-limited shared IPs (CI, cloud agents); the fallback
# pulls the latest rust-just from PyPI, which has no such limit.
bootstrap: ## Level 1 — install base toolchain (uv + just) if missing, then verify
	@if command -v uv >/dev/null 2>&1; then \
		echo -e "[$(CHECK)] uv already installed"; \
	else \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	@if command -v just >/dev/null 2>&1; then \
		echo -e "[$(CHECK)] just already installed"; \
	else \
		echo "Installing just to $(HOME)/.local/bin..."; \
		mkdir -p "$(HOME)/.local/bin"; \
		curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "$(HOME)/.local/bin" \
		|| { \
			echo "just.systems installer failed — falling back to PyPI (rust-just) via uv..."; \
			PATH="$(HOME)/.local/bin:$$PATH" uv tool install rust-just; \
		}; \
	fi
	@PATH="$(HOME)/.local/bin:$$PATH" $(MAKE) --no-print-directory check
	@echo ""
	@echo -e "Bootstrap complete. If 'just' or 'uv' is not found in new shells, add"
	@echo -e "$(HOME)/.local/bin to your PATH ($(YELLOW)SET_PATH=$(HOME)/.local/bin make set-path$(NC) for zsh)."
	@echo -e "Next: $(BLUE)just setup$(NC)"

## `make check` Example Output

### Success case
# Checking dependencies...
# === System Requirements Status ===
# [✓] Just
# [✓] uv
# All dependencies are installed!

### Failure case
# Checking dependencies...
# === System Requirements Status ===
# [✓] just
# [✗] uv (make install-uv)

# Found 1 missing deps: uv
# make: *** [check] Error 1

check: ## Check system requirements
	@echo "Checking dependencies..."
	@echo "=== System Requirements Status ==="
	@ERROR_COUNT=0; \
	CHECK_CMD_NAME="just"; \
	CHECK_CMD_INSTALL="install-just"; \
	if [ $(shell command -v just >/dev/null 2>&1 && echo "0" || echo "1" ) -eq 0 ] ; then \
		printf "[$(CHECK)] $${CHECK_CMD_NAME}\n"; \
	else \
		printf "[$(CROSS)] $${CHECK_CMD_NAME} ($(GREEN)make $${CHECK_CMD_INSTALL}$(NC))\n"; \
		ERROR_COUNT=$$((ERROR_COUNT + 1)); \
		MISSING_DEPS="$${CHECK_CMD_NAME}$${MISSING_DEPS:+,} $${MISSING_DEPS}"; \
	fi; \
	CHECK_CMD_NAME="uv"; \
	CHECK_CMD_INSTALL="install-uv"; \
	if [ $(shell command -v uv >/dev/null 2>&1 && echo "0" || echo "1" ) -eq 0 ] ; then \
		printf "[$(CHECK)] $${CHECK_CMD_NAME}\n"; \
	else \
		printf "[$(CROSS)] $${CHECK_CMD_NAME} ($(GREEN)make $${CHECK_CMD_INSTALL}$(NC))\n"; \
		ERROR_COUNT=$$((ERROR_COUNT + 1)); \
		MISSING_DEPS="$${CHECK_CMD_NAME}$${MISSING_DEPS:+,} $${MISSING_DEPS}"; \
	fi; \
	CHECK_CMD_NAME="docker"; \
	if [ $(shell command -v docker >/dev/null 2>&1 && echo "0" || echo "1" ) -eq 0 ] ; then \
		printf "[$(CHECK)] $${CHECK_CMD_NAME} (optional)\n"; \
	else \
		printf "[$(DASH)] $${CHECK_CMD_NAME} (optional — only for $(CYAN)just docker-web$(NC); $(GREEN)make install-docker$(NC))\n"; \
	fi; \
	if [ "$${ERROR_COUNT}" = "0" ]; then \
		echo -e "$(GREEN)All dependencies are installed!$(NC)"; \
	else \
		echo ""; \
		echo -e "$(RED)Found $$ERROR_COUNT missing deps: $${MISSING_DEPS}$(NC)"; \
		exit 1; \
	fi

hook-check: ## ITM-022 — verify lefthook + downstream hook tools on PATH
	@echo "Checking hook toolchain..."
	@echo "=== Hook Toolchain Status ==="
	@ERROR_COUNT=0; MISSING=""; \
	for TOOL in lefthook gitleaks bun uv editorconfig-checker yamllint codespell; do \
		if command -v $${TOOL} >/dev/null 2>&1; then \
			printf "[$(CHECK)] %s\n" "$${TOOL}"; \
		else \
			printf "[$(CROSS)] %s\n" "$${TOOL}"; \
			ERROR_COUNT=$$((ERROR_COUNT + 1)); \
			MISSING="$${MISSING:+$${MISSING} }$${TOOL}"; \
		fi; \
	done; \
	if [ "$${ERROR_COUNT}" = "0" ]; then \
		echo "$(GREEN)All hook tools are installed!$(NC)"; \
	else \
		echo ""; \
		echo "$(RED)Missing: $${MISSING}$(NC)"; \
		echo "Install via:"; \
		echo "  scripts/install-lefthook.sh   (lefthook)"; \
		echo "  scripts/install-gitleaks.sh   (gitleaks)"; \
		echo "  scripts/install-bun.sh        (bun; required for commitlint)"; \
		echo "  uvx yamllint codespell  (Python tools via uv)"; \
		echo "  bunx --bun editorconfig-checker  (matches lefthook invocation)"; \
		exit 1; \
	fi

install-just: ## Print install just command and where to find install options
	@echo "just installation command:"
	@echo -e "${CYAN}curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin${NC}"
	@echo "or"
	@echo -e "${CYAN}make install-just-force${NC}"
	@echo "NOTE:change ~/.local/bin to the desired installation directory"
	@echo -e "PyPI fallback (no GitHub API rate limit): ${CYAN}uv tool install rust-just${NC}"
	@echo "Find other install options here: https://github.com/casey/just"
	@echo -e "To setup just PATH, run: ${YELLOW}SET_PATH=$(HOME)/.local/bin make set-path${NC}"

install-just-force: ## Install just to ~/.local/bin (PyPI fallback if uv present)
	@echo "Installing just to $(HOME)/.local/bin..."
	@mkdir -p "$(HOME)/.local/bin"
	@curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "$(HOME)/.local/bin" \
	|| { \
		echo "just.systems installer failed — falling back to PyPI (rust-just) via uv..."; \
		if PATH="$(HOME)/.local/bin:$$PATH" command -v uv >/dev/null 2>&1; then \
			PATH="$(HOME)/.local/bin:$$PATH" uv tool install rust-just; \
		else \
			echo -e "$(CROSS) uv not found — install it first ($(YELLOW)make install-uv-force$(NC)) and retry,"; \
			echo "  or see other just install options: https://github.com/casey/just"; \
			exit 1; \
		fi; \
	}
	@echo -e "If $(HOME)/.local/bin is not on your PATH, add it (bash: ~/.bashrc, zsh:"
	@echo -e "$(YELLOW)SET_PATH=$(HOME)/.local/bin make set-path$(NC)), then open a new terminal."


install-uv: ## Print install uv command and where to find install options
	@echo "uv installation command:"
	@echo -e "${CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
	@echo "or"
	@echo -e "${CYAN}make install-uv-force${NC}"
	@echo "Find other install options here: https://docs.astral.sh/uv/getting-started/installation/"
	@echo -e "To setup uv PATH, run: ${YELLOW}SET_PATH=$(HOME)/.local/bin make set-path${NC}"

install-uv-force: ## Install uv and add it to PATH
	@echo "Installing uv..."
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "Adding uv's typical installation directory (~/.local/bin) to PATH in ~/.zshenv..."
	@UV_INSTALL_PATH="$(HOME)/.local/bin"; \
	if ! awk -v path="$${UV_INSTALL_PATH}" ' \
		BEGIN {found=0} \
		/^export PATH=/ { \
			if (index($$0, path) > 0) { \
				found=1; \
				exit; \
			} \
		} \
		END {exit !found}' "$(HOME)/.zshenv"; then \
		echo "export PATH=\"$$PATH:$${UV_INSTALL_PATH}\"" >> "$(HOME)/.zshenv"; \
		echo -e "$(GREEN)Added PATH entry:$(NC) $$PATH:$${UV_INSTALL_PATH}"; \
		echo -e "Run $(BLUE)source $(HOME)/.zshenv$(NC) to apply changes"; \
	else \
		echo -e "$(CHECK) PATH already contains $${UV_INSTALL_PATH}"; \
	fi
	@echo "Please run 'source ~/.zshenv' or open a new terminal to update your PATH if changes were made."

install-docker: ## OPTIONAL — print Docker install instructions (needed only for `just docker-web`)
	@echo "Docker is OPTIONAL for this project — only the container image build"
	@echo "(just docker-web) needs it. Everything else runs without Docker."
	@echo ""
	@echo "Linux installation command (Docker convenience script):"
	@echo -e "${CYAN}curl -fsSL https://get.docker.com | sh${NC}"
	@echo "or"
	@echo -e "${CYAN}make install-docker-force${NC}"
	@echo "macOS/Windows: install Docker Desktop — https://docs.docker.com/get-docker/"

install-docker-force: ## OPTIONAL — install Docker engine via convenience script (Linux only)
	@if [ "$$(uname -s)" != "Linux" ]; then \
		echo -e "$(RED)install-docker-force supports Linux only.$(NC)"; \
		echo "macOS/Windows: install Docker Desktop — https://docs.docker.com/get-docker/"; \
		exit 1; \
	fi
	@echo "Installing Docker engine via https://get.docker.com ..."
	@curl -fsSL https://get.docker.com | sh
	@echo -e "$(CHECK) Docker installed. You may need to add your user to the docker group:"
	@echo -e "${CYAN}sudo usermod -aG docker $$USER && newgrp docker${NC}"

# Flox is OPTIONAL — one of the three first-class toolchain provisioners
# (native installs / mise / flox; see docs/adr/0005). Nothing in the project
# requires it; `flox activate` simply provisions the same 10-tool set declared
# in .flox/env/manifest.toml. Installation is platform-specific and may need
# sudo, so this target prints the commands rather than running them.
install-flox: ## (Optional) Print flox install instructions (toolchain provisioner; see docs/adr/0005)
	@echo "flox is OPTIONAL — it provisions the dev toolchain declared in .flox/ (see docs/adr/0005)."
	@echo ""
	@echo "macOS (Homebrew):"
	@echo -e "  ${CYAN}brew install flox${NC}"
	@echo ""
	@echo "Linux (Debian/Ubuntu — download the .deb, then):"
	@echo -e "  ${CYAN}sudo apt install ./flox.x86_64-linux.deb${NC}"
	@echo "Linux (Fedora/RHEL — download the .rpm, then):"
	@echo -e "  ${CYAN}sudo dnf install ./flox.x86_64-linux.rpm${NC}"
	@echo ""
	@echo "Downloads and all install options (incl. nix profile): https://flox.dev/docs/install-flox/"
	@echo ""
	@echo -e "Then run ${YELLOW}flox activate${NC} from the repo root to enter the environment."

set-path: ## Add SET_PATH to PATH in .zshenv if not already present
	@if [ -z "$(SET_PATH)" ]; then \
		echo -e "$(RED)Error: SET_PATH must be set$(NC)"; \
		echo -e "Usage: $(BLUE)make test2 SET_PATH=/your/path$(NC)"; \
		exit 1; \
	fi; \
	if ! awk -v path="$(SET_PATH)" ' \
		BEGIN {found=0} \
		/^export PATH=/ { \
			if (index($$0, path) > 0) { \
				found=1; \
				exit; \
			} \
		} \
		END {exit !found}' "$(HOME)/.zshenv"; then \
		echo "export PATH=\"\$$PATH:$(SET_PATH)\"" >> "$(HOME)/.zshenv"; \
		echo -e "$(GREEN)Added PATH entry:$(NC) \$$PATH:$(SET_PATH)"; \
		echo -e "Run $(BLUE)source $(HOME)/.zshenv$(NC) to apply changes"; \
	else \
		echo -e "$(CHECK) PATH already contains $(SET_PATH)"; \
	fi

help: ## The help command - this command
	@echo ""
	@echo "Purpose of this Makefile:"
	@echo -e "  To make it easy to check for and install"
	@echo -e "  the main dependencies because almost everyone has $(GREEN)make$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(CYAN)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
