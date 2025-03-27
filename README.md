# Face Recognition Attendance System

A comprehensive Python-based face recognition attendance management system designed for educational institutions. The application leverages advanced computer vision techniques to automate attendance tracking through webcam detection and provides robust data management and reporting capabilities.

## Features

- Student management (add, edit, view, delete)
- Attendance tracking (mark, view, report)
- Face recognition for automated attendance (when running locally)
- Data export for reporting
- Modern and responsive user interface

## Technologies Used

- Python backend
- Face recognition library (for local deployment)
- OpenCV for image processing
- Flask web framework
- SQLite database
- Bootstrap for frontend styling

## Deployment Guide for PythonAnywhere

### Prerequisites

1. A PythonAnywhere account (www.pythonanywhere.com)
2. Git installed on your local machine (for cloning the repository)

### Step 1: Clone the Repository

1. Log in to your PythonAnywhere account
2. Open a Bash console from the Dashboard
3. Clone this repository:
   ```
   git clone https://github.com/yourusername/face-recognition-attendance.git
   ```

### Step 2: Set Up a Virtual Environment

1. In the PythonAnywhere Bash console, navigate to your project directory:
   ```
   cd face-recognition-attendance
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```

### Step 3: Install Dependencies

1. Install the required packages from the requirements file:
   ```
   pip install -r pythonanywhere_requirements.txt
   ```

### Step 4: Configure the Web App

1. Go to the Web tab in your PythonAnywhere dashboard
2. Click on "Add a new web app"
3. Choose your domain name
4. Select "Manual configuration"
5. Choose Python version (Python 3.10 or 3.11 recommended)

### Step 5: Configure WSGI File

1. In the Web tab, click on the WSGI file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
2. Replace the contents with:
   ```python
   import sys
   import os

   # Add your project path to the sys.path
   project_home = '/home/yourusername/face-recognition-attendance'
   if project_home not in sys.path:
       sys.path = [project_home] + sys.path

   # Import your app from app.py
   from app import app as application
   ```

3. Save the file

### Step 6: Configure Static Files

1. In the Web tab, under "Static files", add the following:
   - URL: `/static/`
   - Directory: `/home/yourusername/face-recognition-attendance/static/`

### Step 7: Create Database

1. Return to Bash console (make sure virtual environment is activated)
2. Launch Python console:
   ```
   python
   ```
3. Create the database tables:
   ```python
   from app import app, db
   with app.app_context():
       db.create_all()
   exit()
   ```

### Step 8: Reload the Web App

1. In the Web tab, click the "Reload" button

Your attendance system should now be running on your PythonAnywhere domain (yourusername.pythonanywhere.com).

## Running Locally with Face Recognition

When running locally, you can take advantage of the full face recognition capabilities:

1. Clone the repository to your local machine
2. Install the dependencies from pythonanywhere_requirements.txt
3. Run the application:
   ```
   python main.py
   ```
4. Open a browser and navigate to `http://localhost:5001`

## Notes for Local Development with Face Recognition

- OpenCV and face_recognition libraries require additional system dependencies
- On Windows, make sure to install Visual C++ Build Tools
- On Linux, install required packages: cmake, libsm6, libxext6, libxrender-dev
- On macOS, install required packages via Homebrew: cmake

## License

This project is licensed under the MIT License - see the LICENSE file for details.