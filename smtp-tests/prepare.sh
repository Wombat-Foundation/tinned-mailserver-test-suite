#!/bin/bash

# Load the configuration variables
source vars.conf


# Use `envsubst` to replace variables in the conf templates with the actual values
# envsubst <input.conf >output.conf
if [[ ! -d ${CONFIG_PATH} ]]; then
	mkdir ${CONFIG_PATH}
fi
for T in $(ls -1 templates/*.conf | xargs -n 1 basename); do
	echo "Process ... ${T}"
	envsubst <${TEMPLATE_PATH}/${T} >${CONFIG_PATH}/${T}
done
