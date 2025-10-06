#!/usr/bin/env python3
import sys
import os

# Add the project directory to Python path
project_home = '/home/yourusername/AGTDesigner_deployment'  # Update this path to match your PythonAnywhere directory
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Change to the project directory
os.chdir(project_home)

# Import the Flask app
from app import app as application
