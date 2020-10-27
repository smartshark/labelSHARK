#!/bin/sh
PLUGIN_PATH=$1
cd $PLUGIN_PATH

python3.6 $PLUGIN_PATH/setup.py install --user
wget --quiet --directory-prefix=$PLUGIN_PATH/classifier https://smartshark2.informatik.uni-goettingen.de/classifier/ft_title_clf.p >>/dev/null
wget --quiet --directory-prefix=$PLUGIN_PATH/classifier https://smartshark2.informatik.uni-goettingen.de/classifier/ft_text_clf.p >>/dev/null
