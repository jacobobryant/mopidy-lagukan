#!/bin/bash
set -e
set -x
sudo python2 setup.py sdist bdist_wheel
python2 -m twine upload dist/*
rm dist/*
