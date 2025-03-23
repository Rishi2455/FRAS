from app import app

if __name__ == "__main__":
    # Use a different port to avoid conflict with the 'Start application' workflow
    app.run(host="0.0.0.0", port=5001, debug=True)