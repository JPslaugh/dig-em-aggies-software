#!/bin/bash
cd "$(dirname "$0")"
pip3 install -r requirements.txt --quiet --user
python3 main.py
