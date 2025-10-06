#!/bin/bash
# Direct run command for CodeRunner

# Deactivate any virtual environment
unset VIRTUAL_ENV
unset CONDA_DEFAULT_ENV

# Force use system Python
/usr/bin/python3 app.py
