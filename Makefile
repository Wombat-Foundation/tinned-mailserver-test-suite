PYTHON = python3

.DEFAULT_GOAL := _help

.PHONY: all
all: format lint clean build paper docs bundle ##H Full pipeline: format, lint, clean, build, paper, docs, bundle

# --- Print Helpers ---
define print_info
	printf "\033[1;36m%s\033[0m\n" "$(1)"
endef
define print_success
	printf "\033[1;34m✓ %s\033[0m\n" "$(1)"
endef

# LINT_LOCS_PY ?= $$(git ls-files '*.py')

.PHONY: format
format: ##H Format source files
	-shfmt -w $$(git ls-files '*.sh')
# 	-black $(LINT_LOCS_PY)
# 	-isort $(LINT_LOCS_PY)
	-prettier -w .
	-pre-commit run --all-files


.PHONY: lint
lint: shellcheck flake8 ##H Lint sources

.PHONY: shellcheck
shellcheck: ##H Lint shell scripts
	@$(call print_info,Linting shell scripts with shellcheck...)
	shellcheck $$(git ls-files '*.sh')
	@$(call print_success,Shellcheck complete.)

.PHONY: flake8
flake8: ##H Lint python files
	@$(call print_info,Linting python files with flake8...)
	@if git ls-files '*.py' | grep -q .; then \
		flake8 $$(git ls-files '*.py'); \
	else \
		echo "No python files found."; \
	fi
	@$(call print_success,Flake8 complete.)


# .PHONY: clean
# clean: ##H Remove build artifacts
# 	rm -f *.o bundle.zip synthesizer dendro firefighter leontovich_fast landscape_txz
# 	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: _help
_help: ##H Show this help
	@printf "\nUsage: make <command>\n\n"
	@grep -E '^[a-zA-Z_/.-]+:.*?##H' $(MAKEFILE_LIST) | sort | sed 's/:.*##H /\t/' | expand -t 20 | sed 's/^/  /'
	@printf "\n"
