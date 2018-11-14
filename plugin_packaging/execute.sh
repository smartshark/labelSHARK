#!/bin/sh

PLUGIN_PATH=$1

COMMAND="python3.5 $PLUGIN_PATH/smartshark_plugin.py -u ${2} -DB ${6} -H ${7} -p ${8} -is ${11} -ap ${12}"

if [ ! -z ${3+x} ] && [ ${3} != "None" ]; then
	COMMAND="$COMMAND --project_name ${3}"
fi

if [ ! -z ${4+x} ] && [ ${4} != "None" ]; then
	COMMAND="$COMMAND --db-user ${4}"
fi

if [ ! -z ${5+x} ] && [ ${5} != "None" ]; then
	COMMAND="$COMMAND --db-password ${5}"
fi

if [ ! -z ${9+x} ] && [ ${9} != "None" ]; then
	COMMAND="$COMMAND --db-authentication ${9}"
fi

if [ ! -z ${10+x} ] && [ ${10} != "None" ]; then
	COMMAND="$COMMAND --ssl"
fi

if [ ! -z ${13+x} ] && [ ${13} != "None" ]; then
    COMMAND="$COMMAND -la ${13}"
fi

if [ ! -z ${14+x} ] && [ ${14} != "None" ]; then
    COMMAND="$COMMAND -ll ${14}"
fi

if [ ! -z ${15+x} ] && [ ${15} != "None" ]; then
    COMMAND="$COMMAND -ph ${15}"
fi

if [ ! -z ${16+x} ] && [ ${16} != "None" ]; then
    COMMAND="$COMMAND -pp ${16}"
fi

$COMMAND
