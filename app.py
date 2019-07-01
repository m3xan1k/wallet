from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
from models import *


# Routes
@app.route('/')
def index():
    return 'Index'


if __name__ == '__main__':
    app.run(debug=True)