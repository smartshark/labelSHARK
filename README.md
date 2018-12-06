# labelSHARK

[![Build Status](https://travis-ci.org/smartshark/labelSHARK.svg?branch=master)](https://travis-ci.org/smartshark/labelSHARK)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://smartshark.github.io/labelSHARK/)

Commit labeling for smartSHARK.

If you want to include a labeling approach read the full documentation provided above.

## Install

### via PIP
```bash
pip install https://github.com/smartshark/labelSHARK/zipball/master
```

### via setup.py
```bash
python setup.py install
```

## Run Tests
```bash
python setup.py test
```

## Execution for smartSHARK

LabelSHARK needs only access to the MongoDB and the URL of the repository which commits should be labeled. 
It requires that [linkSHARK](https://github.com/smartshark/linkSHARK) has already been run.

```bash
# This uses all issue tracking systems registered and mined for the project.
# It also uses every labeling approach available.
python smartshark_plugin.py -U $DBUSER -P $DBPASS -DB $DBNAME -u $REPOSITORY_GIT_URI -a $AUTHENTICATION_DB --approaches all

# we can also limit, e.g., to SZZ and documentation labeling
python smartshark_plugin.py -U $DBUSER -P $DBPASS -DB $DBNAME -u $REPOSITORY_GIT_URI -a $AUTHENTICATION_DB --approaches adjustedszz,documentation
```
