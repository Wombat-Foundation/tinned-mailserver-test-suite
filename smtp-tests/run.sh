#!/bin/bash
#
VERSION="0.0.5"
#


# Color definition
GREEN='\e[0;32m'
YELLOW='\e[0;33m'
RED='\e[0;31m'
# shellcheck disable=SC2034
BLUE='\e[0;36m'
RST='\e[0m'

#
# Help screen
#
function help_screen () {
    echo
    echo "Usage: $(basename "$0") [-hv] [--verbose]"
    echo "  -h  --help                      print this usage and exit"
    echo "  -v  --version                   print version information and exit"
    echo "      --verbose                   Show verbose details like SMTP transaction for failed tests"
    echo
}

function version_screen
{
    echo
    echo "$(basename "$0") Version $VERSION"
    echo
}

VERBOSE=0
while [ $# -gt 0 ]; do
    case $1 in
        # General parameter
        -h|--help)
            help_screen
            exit 0
            ;;

        -v|--version)
            version_screen
            exit 0
            ;;

        --verbose)
            VERBOSE=1
            shift 1
            ;;
        *)
            errorout "ERROR: Unknown option '$1'."
            help_screen
            exit 1
            ;;
    esac
done

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
readarray -t TESTCASES < <(find "${CONFIG_PATH}" -name '*.conf' -exec basename {} \; | sort)

# create the log directory if not existing
if [[ ! -d "${LOG_PATH}" ]]; then
	mkdir -p "${LOG_PATH}"
fi

FAILED_TESTS=0
TOTAL_TESTS=0

for TC in "${TESTCASES[@]}"; do
	[[ -z "$TC" ]] && continue
	TOTAL_TESTS=$((TOTAL_TESTS + 1))

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
	if [[ "${TC_RC}" -ne "${TC_RC_EXP}" ]] && [[ "${VERBOSE}" -eq "1" ]]; then
		echo -e "${YELLOW}Debug: Full log:${RST}"
		sed 's/^/  /' "${LOG_PATH}/${TC_NAME}.log"
		echo
	fi
done

if [[ ${FAILED_TESTS} -gt 0 ]]; then
	echo -e "\n${RED}Error: ${FAILED_TESTS} tests failed.${RST}"
	exit 1
else
	echo -e "\n${GREEN}All ${TOTAL_TESTS} tests passed successfully.${RST}"
	exit 0
fi
