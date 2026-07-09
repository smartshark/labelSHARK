#!/bin/bash
PLUGIN_PATH=$1
cd $PLUGIN_PATH

if [ ! -z "$SLURM_JOB_ID" ]; then
    python3.6 $PLUGIN_PATH/setup.py install --user
else
    python $PLUGIN_PATH/setup.py install
fi

wget --quiet --directory-prefix=$PLUGIN_PATH/classifier https://smartshark2.informatik.uni-goettingen.de/classifier/ft_title_clf.p >>/dev/null
wget --quiet --directory-prefix=$PLUGIN_PATH/classifier https://smartshark2.informatik.uni-goettingen.de/classifier/ft_text_clf.p >>/dev/null
