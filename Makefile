.PHONY: lint lint-shell lint-python

# Find all shell scripts (files with .sh extension or with a shell shebang)
SHELL_FILES := $(shell find . -type f -name "*.sh" -not -path "./.git/*")
# Find all python files
PYTHON_FILES := $(shell find . -type f -name "*.py" -not -path "./.git/*")

lint: lint-shell lint-python

lint-shell:
	@if [ -n "$(SHELL_FILES)" ]; then \
		echo "Linting shell scripts with shellcheck..."; \
		shellcheck $(SHELL_FILES); \
	else \
		echo "No shell scripts found for linting."; \
	fi

lint-python:
	@if [ -n "$(PYTHON_FILES)" ]; then \
		echo "Linting python files with flake8..."; \
		flake8 $(PYTHON_FILES); \
	else \
		echo "No python files found for linting."; \
	fi
