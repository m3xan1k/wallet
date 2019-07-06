import os
from os.path import join, dirname, realpath


SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'very secret csrf token'
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/uploads')