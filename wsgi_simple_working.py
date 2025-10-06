#!/usr/bin/env python3
import sys
import os

# Use the directory where this WSGI file is located
project_home = os.path.dirname(os.path.abspath(__file__))

# Add the project directory to Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Change to the project directory
os.chdir(project_home)

# Import the Flask app
from app import app as application
