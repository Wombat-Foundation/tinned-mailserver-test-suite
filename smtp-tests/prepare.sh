#!/bin/bash

# Load the configuration variables
source vars.conf

if [[ ! -d ${TEMPLATE_PATH} ]]; then
	echo "Error: Template directory ${TEMPLATE_PATH} not found."
	exit 1
fi

if [[ ! -d ${CONFIG_PATH} ]]; then
	mkdir -p ${CONFIG_PATH}
fi

for T in $(ls -1 ${TEMPLATE_PATH}/*.conf 2>/dev/null | xargs -n 1 basename 2>/dev/null); do
	if [[ -n "$T" ]]; then
		echo "Process ... ${T}"
		envsubst <${TEMPLATE_PATH}/${T} >${CONFIG_PATH}/${T}
	fi
done
