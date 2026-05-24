SHELL := /bin/zsh

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

.PHONY: all check hook-check install-uv install-just set-path help install-just-force install-uv-force

all: help

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
		echo "  uvx editorconfig-checker yamllint codespell  (Python tools — try uvx)"; \
		exit 1; \
	fi

install-just: ## Print install just command and where to find install options
	@echo "just installation command:"
	@echo -e "${CYAN}curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin${NC}"
	@echo "or"
	@echo -e "${CYAN}make install-just-force${NC}"
	@echo "NOTE:change ~/bin to the desired installation directory"
	@echo "Find other install options here: https://github.com/casey/just"
	@echo -e "To setup just PATH, run: ${YELLOW}SET_PATH=$(HOME)/bin make set-path${NC}"

install-just-force: ## Install just and add it to PATH
	@echo "Installing just to ~/bin..."
	@curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to $(HOME)/bin
	@echo "Adding $(HOME)/bin to PATH in $(HOME)/.zshenv..."
	@if ! awk -v path="$(HOME)/bin" ' \
		BEGIN {found=0} \
		/^export PATH=/ { \
			if (index($$0, path) > 0) { \
				found=1; \
				exit; \
			} \
		} \
		END {exit !found}' "$(HOME)/.zshenv"; then \
		echo "export PATH=\"$$PATH:$(HOME)/bin\"" >> "$(HOME)/.zshenv"; \
		echo -e "$(GREEN)Added PATH entry:$(NC) $$PATH:$(HOME)/bin"; \
		echo -e "Run $(BLUE)source $(HOME)/.zshenv$(NC) to apply changes"; \
	else \
		echo -e "$(CHECK) PATH already contains $(HOME)/bin"; \
	fi
	@echo "Please run 'source ~/.zshenv' or open a new terminal to update your PATH."


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
