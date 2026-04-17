#!/bin/bash
cd "$(dirname "$0")"
export QT_MAC_WANTS_LAYER=1

if [ "$1" == "demo" ]; then
    python3 demo.py
else
    python3 main.py
fi
