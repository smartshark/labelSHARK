#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

if not sys.version_info[0] == 3:
    print('only python3 supported!')
    sys.exit(1)
if not sys.version_info[1] > 5:
    print('only python > 3.5 supported, got: {}.{}'.format(sys.version_info[0], sys.version_info[1]))
    sys.exit(1)

setup(
    name='labelSHARK',
    version='2.2.1',
    description='Commit labeling for smartSHARK.',
    install_requires=['pandas', 'mongoengine', 'pymongo', 'pycoshark>=1.3.1', 'skift',
                      'fasttext @ https://github.com/facebookresearch/fastText/tarball/master#egg-fasttext-0.10.0',],
    dependency_links=['https://github.com/facebookresearch/fastText/tarball/master#egg-fasttext-0.10.0'],
    author='atrautsch',
    author_email='alexander.trautsch@cs.uni-goettingen.de',
    url='https://github.com/smartshark/labelSHARK',
    download_url='https://github.com/smartshark/labelSHARK/zipball/master',
    test_suite='labelSHARK.tests',
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache2.0 License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
