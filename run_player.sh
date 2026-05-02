#!/bin/bash
cd "$(dirname "$0")"
PYTHONPATH="$(pwd)/venv/lib/python3.12/site-packages:$PYTHONPATH" python3 media_player.py
