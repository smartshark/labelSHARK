#!/bin/bash

current=`pwd`
mkdir -p /tmp/labelSHARK/
cp * /tmp/labelSHARK/
cp ../setup.py /tmp/labelSHARK/
cp -R ../labelSHARK/* /tmp/labelSHARK/
cd /tmp/labelSHARK/

tar -cvf "$current/labelSHARK_plugin.tar" --exclude=*.tar --exclude=build_plugin.sh --exclude=tests --exclude=__pycache__ --exclude=*.pyc *
