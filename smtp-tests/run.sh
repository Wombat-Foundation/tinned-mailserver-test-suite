#!/bin/bash
#
VERSION="0.0.6"
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
	echo "  -l  --cat-list                  List all available categories"
	echo "  -c  --category CATEGORY         Only run tests from a specific category"
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
		-l|--cat-list)
			LIST_CATEGORIES=1
			shift 1
			;;
		-c|--category)
			if [[ ! -z "$2" ]]; then
				RUN_CATEGORY=$2
				shift 2
			else
				echo -e "${RED}ERROR${RST}: Option '--category' requires an argument."
				exit 1
			fi
			;;
		*)
			echo -e "${RED}ERROR${RST}: Unknown option '$1'."
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
	EXPECTED_RC=0
	unset CATEGORY
	# Read only the first 20 comments lines with "=" in them
	while IFS= read -r CONF_LINE; do
		# Extract the part after "# "
		LOAD_VAR="${CONF_LINE:2}"
		# Only extract known variables
		if [[ "$LOAD_VAR" =~ ^((EXPECTED_RC)|(CATEGORY))+=.*$ ]]; then
			declare -x "$LOAD_VAR"
		fi
	done < <(head -n 20 "${CONFIG_PATH}/${TC}" | grep '# .*=')

	# LIST CATEGORIES: collect all category names
	if [[ ! -z "${LIST_CATEGORIES}" ]]; then
		ALL_CATEGORIES="${ALL_CATEGORIES},${CATEGORY}"
		continue
	fi

	# Run only specified category
	if [[ ! -z "${RUN_CATEGORY}" ]]; then
		# Limit the test cases to a category
		if [[ "$CATEGORY" != *"$RUN_CATEGORY"* ]]; then
			# Skip non-matching test case
			continue
		fi
	fi

	# Get testcase name from filename
	TC_NAME="${TC%.conf}"

	swaks --config "${CONFIG_PATH}/${TC}" >"${LOG_PATH}/${TC_NAME}.log" 2>&1
	TC_RC=$?

	# Determine result and color
	if [[ "${TC_RC}" -eq "${EXPECTED_RC}" ]]; then
		RESULT_STR="PASSED (${TC_RC})"
		COLOR="${GREEN}"
	else
		RESULT_STR="FAILED (${TC_RC})"
		COLOR="${RED}"
		FAILED_TESTS=$((FAILED_TESTS + 1))
	fi

	# Alignment logic: align filenames at column 75
	PREFIX="Testcase ... ${RESULT_STR} "
	PREFIX_LEN=${#PREFIX}
	DOT_COUNT=$((30 - PREFIX_LEN))
	[[ $DOT_COUNT -lt 1 ]] && DOT_COUNT=1
	DOTS=$(printf "%${DOT_COUNT}s" | tr ' ' '.')

	echo -e "Testcase ... ${COLOR}${RESULT_STR}${RST} ${DOTS} ${TC_NAME}"
	if [[ "${VERBOSE}" -eq "1" ]]; then
		echo -e "    ${BLUE}Expected RC: ${EXPECTED_RC}${RST}"
		echo -e "    ${BLUE}Category   : ${CATEGORY}${RST}"
	fi

	# If test failed, show the full swaks log for debugging
	if [[ "${TC_RC}" -ne "${EXPECTED_RC}" ]] && [[ "${VERBOSE}" -eq "1" ]]; then
		echo -e "${YELLOW}Debug: Full log:${RST}"
		sed 's/^/  /' "${LOG_PATH}/${TC_NAME}.log"
		echo
	fi
done

# LIST CATEGORIES: generate the list of categories
if [[ ! -z "${LIST_CATEGORIES}" ]]; then
	echo "Available categories:"
	echo "${ALL_CATEGORIES}" | tr ',' '\n' | grep -v '^$' | sort -u | sed -e 's/"//g' -e 's/^/  - /'
	echo
	exit 0
fi

if [[ ${FAILED_TESTS} -gt 0 ]]; then
	echo -e "\n${RED}Error: ${FAILED_TESTS} tests failed.${RST}"
	exit 1
else
	echo -e "\n${GREEN}All ${TOTAL_TESTS} tests passed successfully.${RST}"
	exit 0
fi
