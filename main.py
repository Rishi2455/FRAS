
from flask import Flask
from app import app
from routes import *

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        # Fall back to basic web server if face recognition fails
        from werkzeug.serving import run_simple
        run_simple('0.0.0.0', 5000, app, use_reloader=True)
