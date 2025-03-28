"""
Simple database fix script to update the models.
"""
from app import app, db

print("Starting database fix...")

with app.app_context():
    # This will update the schema based on models.py
    print("Creating tables with updated schema...")
    db.create_all()
    print("Database schema updated!")

print("Fix complete. Restart the application to apply changes.")