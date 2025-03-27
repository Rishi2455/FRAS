import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")

# Configure the database to use SQLite
# This will work both locally and on PythonAnywhere
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or \
    "sqlite:///" + os.path.join(basedir, "attendance.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

    db.create_all()

# Import routes after initializing app to avoid circular imports
from routes import *  # noqa: E402, F401