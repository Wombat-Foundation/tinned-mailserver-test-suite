#!/bin/bash

# Color definition
GREEN='\e[0;32m'
YELLOW='\e[0;33m'
RED='\e[0;31m'
BLUE='\e[0;36m'
RST='\e[0m'

if [[ ! -f "./vars.conf" ]]; then
	echo -e "${RED}Error: vars.conf not found.${RST}"
	echo -e "Please copy vars.example.conf to vars.conf and fill in your settings."
	exit 1
fi

source ./vars.conf

# call prepare script to populate the settings into the config files
bash ./prepare.sh
echo

CMAX=20

# get the list of testcases
TESTCASES=$(find ${CONFIG_PATH} -name '*.conf' | xargs -n 1 basename | sort)

# create the log directory if not existing
if [[ ! -d "${LOG_PATH}" ]]; then
	mkdir -p ${LOG_PATH}
fi

FAILED_TESTS=0

for TC in ${TESTCASES[@]}; do
	TC_RC_EXP=$(echo "${TC}" | sed -E 's/^.*__([0-9]+)\.conf/\1/')

	#echo -e "Testcase ...... ${TC}"
	#echo -e "Expected RC ... ${TC_RC_EXP}"

	swaks --config ${CONFIG_PATH}/${TC} >${LOG_PATH}/${TC/.conf/.log} 2>&1
	TC_RC=$?
	# calculate the amount of characters to align the columns
	CL=$(echo "....." | head -c $((${CMAX}-${#TC_RC})) )
	if [[ "${TC_RC}" -eq "${TC_RC_EXP}" ]]; then
		echo -e "Testcase ...... ${GREEN}PASSED (${TC_RC})${RST} ${CL} ${TC/.conf/}"
	else
		echo -e "Testcase ...... ${RED}FAILED (${TC_RC})${RST} ${CL} ${TC/.conf/}"
		FAILED_TESTS=$((FAILED_TESTS + 1))
	fi
done

if [[ ${FAILED_TESTS} -gt 0 ]]; then
	echo -e "\n${RED}Error: ${FAILED_TESTS} tests failed.${RST}"
	exit 1
else
	echo -e "\n${GREEN}All tests passed successfully.${RST}"
	exit 0
fi
