#!/bin/bash


# hpc special case
if [ ! -z "$SLURM_JOB_ID" ]; then
    module load gcc/9.2.0
fi

PLUGIN_PATH=$1

if [ ! -z "$SLURM_JOB_ID" ]; then
    COMMAND="python3.6 $PLUGIN_PATH/smartshark_plugin.py -DB ${4} -H ${5} -p ${6} --project-name ${10} --approaches ${11}"
else
    COMMAND="python $PLUGIN_PATH/smartshark_plugin.py -DB ${4} -H ${5} -p ${6} --project-name ${10} --approaches ${11}"
fi

if [ ! -z ${2+x} ] && [ ${2} != "None" ]; then
	COMMAND="$COMMAND --db-user ${2}"
fi

if [ ! -z ${3+x} ] && [ ${3} != "None" ]; then
	COMMAND="$COMMAND --db-password ${3}"
fi

if [ ! -z ${7+x} ] && [ ${7} != "None" ]; then
	COMMAND="$COMMAND --db-authentication ${7}"
fi

if [ ! -z ${8+x} ] && [ ${8} != "None" ]; then
	COMMAND="$COMMAND --ssl"
fi

if [ ! -z ${9+x} ] && [ ${9} != "None" ]; then
    COMMAND="$COMMAND --log-level ${9}"
fi

$COMMAND
