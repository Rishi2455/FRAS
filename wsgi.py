"""
WSGI configuration file for PythonAnywhere
"""

import sys
import os

# Add your project path to the sys.path
project_home = u'/home/yourusername/face-recognition-attendance'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import your app from app.py
from app import app as application  # Important: PythonAnywhere looks for 'application'