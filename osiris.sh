#!/bin/bash

source ../envars.env
LD_LIBRARY_PATH="$HOME/.local/lib/:$HOME/.local/lib64/" ../venv370/bin/python3 -m osiris --config-file rules.ini
