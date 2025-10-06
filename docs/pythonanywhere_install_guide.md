# PythonAnywhere Installation Guide

## Step 1: Verify Virtual Environment
```bash
# Check if you're in the correct virtual environment
which python
which pip
# Should show paths like: /home/adamcordova/.virtualenvs/myflaskapp-env/bin/python

# If not in virtual environment, activate it:
source ~/.virtualenvs/myflaskapp-env/bin/activate
```

## Step 2: Upgrade pip and setuptools
```bash
pip install --upgrade pip setuptools wheel
```

## Step 3: Install packages one by one (in order)
```bash
# Core dependencies first
pip install Flask==3.0.2
pip install Werkzeug==3.0.1
pip install Jinja2==3.1.3
pip install itsdangerous==2.1.2
pip install click==8.1.7
pip install MarkupSafe==2.1.5

# Data processing libraries
pip install numpy==1.26.4
pip install pandas==2.2.1
pip install python-dateutil==2.8.2

# Document processing
pip install python-docx==1.1.0
pip install docxtpl==0.16.7
pip install docxcompose==1.4.0
pip install openpyxl==3.1.2

# Image processing
pip install Pillow==10.2.0

# File monitoring
pip install watchdog>=2.1.6
```

## Step 4: Alternative - Install with no build isolation
If individual installations fail, try:
```bash
pip install --no-build-isolation --no-cache-dir pandas==2.2.1
```

## Step 5: Verify installations
```bash
python -c "import pandas; print(pandas.__version__)"
python -c "import flask; print(flask.__version__)"
python -c "import docx; print('python-docx installed')"
```

## Step 6: Check your WSGI configuration
Make sure your WSGI file points to the correct virtual environment and application.
