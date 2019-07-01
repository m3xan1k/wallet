from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect, url_for
from flask.views import MethodView

from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo, Email


app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
from models import *


# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.get(id)


# Forms
class SignUpForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=30)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=80), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', validators=[DataRequired()])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


# Routes
@app.route('/')
def index():
    return render_template('index.html')


class SignUp(MethodView):

    def get(self):
        form = SignUpForm(request.form)
        return render_template('signup.html', form=form)

    def post(self):
        form = SignUpForm(request.form)
        if form.validate_on_submit():
            return redirect(url_for('index'))
            
        return render_template('signup.html', form=form)

app.add_url_rule('/signup', view_func=SignUp.as_view('signup'))


@app.route('/login')
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)