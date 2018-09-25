#!/bin/bash

export LD_LIBRARY_PATH="$HOME/.local/lib/:$HOME/.local/lib64/"
source ../envars.env
source ../venv370/bin/activate
python3 -m osiris -c rules.ini -d || true
deactivate
