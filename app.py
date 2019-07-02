from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect, url_for, flash
from flask.views import MethodView

from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from wtforms import Form
from wtforms import StringField, BooleanField, TextAreaField, PasswordField
from wtforms.validators import InputRequired, Length, EqualTo, Email

from passlib.hash import sha256_crypt


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
    return User.query.get(int(id))


# Forms
class SignUpForm(Form):
    email = StringField('Email', [InputRequired(message='Input Required'), Email(message='Email is not correct')])
    username = StringField('Username', [InputRequired(message='Input Required'), Length(min=4, max=30)])
    password = PasswordField('Password', [InputRequired(message='Input Required'), Length(min=8, max=80), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', [InputRequired(message='Input Required')])


class LoginForm(Form):
    username = StringField('Username', validators=[InputRequired(message='Input Required')])
    password = PasswordField('Password', validators=[InputRequired(message='Input Required')])


# Routes
@app.route('/')
def index():
    return render_template('index.html')


class SignUp(MethodView):

    def get(self):
        form = SignUpForm()
        return render_template('signup.html', form=form)

    def post(self):
        form = SignUpForm(request.form)
        if form.validate():
            email = form.email.data
            username = form.username.data
            hashed_password = sha256_crypt.encrypt(form.password.data)

            new_user = User(email=email, username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            flash('You successfully registered', category='success')

            return redirect(url_for('index'))
   
        return render_template('signup.html', form=form)

app.add_url_rule('/signup', view_func=SignUp.as_view('signup'))


# @app.route('/login')
# def login():
#     return render_template('login.html')


class Login(MethodView):
    
    def get(self):
        form = LoginForm()
        return render_template('login.html', form=form)

    def post(self):
        form = LoginForm(request.form)
        if form.validate():
            user = User.query.filter_by(username=form.username.data).first()
            if user and sha256_crypt.verify(form.password.data, user.password):

                login_user(user)
                flash('You successfully logged in', category='success')
                return redirect(url_for('index'))

            flash('Username or Password is not correct', category='danger')
            return render_template('login.html', form=form)



app.add_url_rule('/login', view_func=Login.as_view('login'))


if __name__ == '__main__':
    app.run(debug=True)