#!/usr/bin/env python3
"""
Simple app runner for CodeRunner play button
"""

import subprocess
import os
import sys

# Change to the script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Deactivate any virtual environment
os.environ.pop('VIRTUAL_ENV', None)
os.environ.pop('CONDA_DEFAULT_ENV', None)

# Run the app with system Python
subprocess.run(['/usr/bin/python3', 'app.py'])
