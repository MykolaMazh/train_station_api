#!/usr/bin/env bash

set -o errexit


pip install -r requirements.txt

python -m pip install Pillow



python manage.py migrate