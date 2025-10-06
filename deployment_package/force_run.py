#!/usr/bin/env python3
# Force run with system Python - bypasses virtual environment issues
import subprocess
import os
import sys

# Force use system Python and deactivate any virtual environment
os.environ.pop('VIRTUAL_ENV', None)
os.environ.pop('CONDA_DEFAULT_ENV', None)

# Run with system Python
subprocess.run(['/usr/bin/python3', 'app.py'])
