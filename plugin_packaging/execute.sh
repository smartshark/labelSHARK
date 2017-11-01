#!/bin/sh

PLUGIN_PATH=$1

COMMAND="python3.5 $PLUGIN_PATH/smartshark_plugin.py -u $2 -DB $5 -H $6 -p $7 -is $10 -ap $11"


if [ ! -z ${3+x} ] && [ ${3} != "None" ]; then
	COMMAND="$COMMAND --db-user ${3}"
fi

if [ ! -z ${4+x} ] && [ ${4} != "None" ]; then
	COMMAND="$COMMAND --db-password ${4}"
fi

if [ ! -z ${8+x} ] && [ ${8} != "None" ]; then
	COMMAND="$COMMAND --db-authentication ${8}"
fi

if [ ! -z ${9+x} ] && [ ${9} != "None" ]; then
	COMMAND="$COMMAND --ssl"
fi

if [ ! -z ${12+x} ] && [ ${12} != "None" ]; then
    COMMAND="$COMMAND -la ${12}"
fi

$COMMAND
