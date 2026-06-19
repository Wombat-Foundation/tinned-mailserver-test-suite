#!/bin/bash
#
# VERSION="0.0.5"
#

# Load the configuration variables
# Use set -a to automatically export all variables so envsubst can see them
set -a
# shellcheck source=/dev/null
source vars.conf
set +a

if [[ ! -d "${TEMPLATE_PATH}" ]]; then
	echo "Error: Template directory ${TEMPLATE_PATH} not found."
	exit 1
fi

if [[ ! -d "${CONFIG_PATH}" ]]; then
	mkdir -p "${CONFIG_PATH}"
fi

for T_PATH in "${TEMPLATE_PATH}"/*.conf; do
	[[ -e "$T_PATH" ]] || continue
	T=$(basename "$T_PATH")
	echo "Process ... ${T}"
	envsubst <"$T_PATH" >"${CONFIG_PATH}/${T}"
done
