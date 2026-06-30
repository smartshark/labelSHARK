#!/bin/bash
PLUGIN_PATH=$1
cd $PLUGIN_PATH

if [ ! -z "$SLURM_JOB_ID" ]; then
    python3.6 -m pip install --user --no-cache-dir --upgrade --upgrade-strategy only-if-needed "pycoshark @ git+https://github.com/smartshark/pycoSHARK.git@2.0.0"
    python3.6 $PLUGIN_PATH/setup.py install --user
else
    python -m pip install --user --no-cache-dir --upgrade --upgrade-strategy only-if-needed "pycoshark @ git+https://github.com/smartshark/pycoSHARK.git@2.0.0"
    python $PLUGIN_PATH/setup.py install
fi

wget --quiet --directory-prefix=$PLUGIN_PATH/classifier https://smartshark2.informatik.uni-goettingen.de/classifier/ft_title_clf.p >>/dev/null
wget --quiet --directory-prefix=$PLUGIN_PATH/classifier https://smartshark2.informatik.uni-goettingen.de/classifier/ft_text_clf.p >>/dev/null
