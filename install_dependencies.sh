#!/bin/bash
#
#

if [[ -d './venv' ]]; then
    echo 'Virtual environment exists, skipping creation'
else
    python3 -m venv venv
    ./venv/bin/pip install -U setuptools pip
    ./venv/bin/pip install -r requirements.txt
fi

if [[ ! -f 'haarcascade_frontalface_default.xml' ]]; then
    wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml
fi
