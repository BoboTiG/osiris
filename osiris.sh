#!/bin/bash

export LD_LIBRARY_PATH="$HOME/.local/lib/:$HOME/.local/lib64/"
source ../envars.env
source ../venv370/bin/activate
python3 -m osiris --config-file rules.ini || true
deactivate
