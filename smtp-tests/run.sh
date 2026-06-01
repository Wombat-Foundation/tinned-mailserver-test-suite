#!/bin/bash

# Color definition
# shellcheck disable=SC2034
GREEN='\e[0;32m'
# shellcheck disable=SC2034
YELLOW='\e[0;33m'
# shellcheck disable=SC2034
RED='\e[0;31m'
# shellcheck disable=SC2034
BLUE='\e[0;36m'
# shellcheck disable=SC2034
RST='\e[0m'

if [[ ! -f "./vars.conf" ]]; then
	echo -e "${RED}Error: vars.conf not found.${RST}"
	echo -e "Please copy vars.example.conf to vars.conf and fill in your settings."
	exit 1
fi

# shellcheck source=/dev/null
source ./vars.conf

# call prepare script to populate the settings into the config files
bash ./prepare.sh
echo

# get the list of testcases
# shellcheck disable=SC2012
readarray -t TESTCASES < <(find "${CONFIG_PATH}" -name '*.conf' -exec basename {} \; | sort)

# create the log directory if not existing
if [[ ! -d "${LOG_PATH}" ]]; then
	mkdir -p "${LOG_PATH}"
fi

FAILED_TESTS=0

for TC in "${TESTCASES[@]}"; do
	[[ -z "$TC" ]] && continue

	# Extract expected return code from filename (e.g., swaks__...__0.conf -> 0)
	if [[ "$TC" =~ __([0-9]+)\.conf$ ]]; then
		TC_RC_EXP="${BASH_REMATCH[1]}"
	else
		TC_RC_EXP=0
	fi

	TC_NAME="${TC%.conf}"

	swaks --config "${CONFIG_PATH}/${TC}" >"${LOG_PATH}/${TC_NAME}.log" 2>&1
	TC_RC=$?

	# Determine result and color
	if [[ "${TC_RC}" -eq "${TC_RC_EXP}" ]]; then
		RESULT_STR="PASSED (${TC_RC})"
		COLOR="${GREEN}"
	else
		RESULT_STR="FAILED (${TC_RC})"
		COLOR="${RED}"
		FAILED_TESTS=$((FAILED_TESTS + 1))
	fi

	# Alignment logic: align filenames at column 75
	PREFIX="Testcase ...... ${RESULT_STR} "
	PREFIX_LEN=${#PREFIX}
	DOT_COUNT=$((75 - PREFIX_LEN))
	[[ $DOT_COUNT -lt 1 ]] && DOT_COUNT=1
	DOTS=$(printf "%${DOT_COUNT}s" | tr ' ' '.')

	echo -e "Testcase ...... ${COLOR}${RESULT_STR}${RST} ${DOTS} ${TC_NAME}"

	# If test failed, show the full swaks log for debugging
	if [[ "${TC_RC}" -ne "${TC_RC_EXP}" ]]; then
		echo -e "${YELLOW}Debug: Full log:${RST}"
		cat "${LOG_PATH}/${TC_NAME}.log" | sed 's/^/  /'
		echo
	fi
done

if [[ ${FAILED_TESTS} -gt 0 ]]; then
	echo -e "\n${RED}Error: ${FAILED_TESTS} tests failed.${RST}"
	exit 1
else
	echo -e "\n${GREEN}All tests passed successfully.${RST}"
	exit 0
fi
