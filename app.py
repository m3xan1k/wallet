from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect, url_for, flash
from flask.views import MethodView

from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from wtforms import Form
from wtforms import StringField, BooleanField, TextAreaField, PasswordField, SelectField, DecimalField
from wtforms.validators import InputRequired, Length, EqualTo, Email, DataRequired

from passlib.hash import sha256_crypt

from flask_migrate import Migrate
from decimal import Decimal
from functools import wraps


app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import *


# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


def legal_wallet(id):
    wallet = db.session.query(Wallet).join(User).filter(Wallet.user_id == current_user.id).filter(Wallet.id == id).first()
    return wallet



# Forms
class SignUpForm(Form):
    email = StringField('Email', [InputRequired(), Email(message='Email is not correct')])
    username = StringField('Username', [InputRequired(), Length(min=4, max=30)])
    password = PasswordField('Password', [InputRequired(), Length(min=8, max=80), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', [InputRequired()])


class LoginForm(Form):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class WalletForm(Form):
    choices = [
        ('cash', 'cash'),
        ('card', 'card'),
        ('bank account', 'bank account'),
        ('digital wallet', 'digital wallet'),
        ('crypto wallet', 'crypto wallet'),
    ]

    name = StringField('Wallet Name', [InputRequired(), Length(min=4, max=30)])
    pay_type = SelectField('Wallet Type', choices=choices, validators=[InputRequired()])
    balance = DecimalField('Balance', default=Decimal('0.00'), validators=[InputRequired()])


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


@app.route('/dashboard')
@login_required
def dashboard():
    wallets = db.session.query(Wallet).join(User).filter(User.username == current_user.username).all()

    balance = sum(map((lambda wallet: wallet.balance), wallets))
    # List of lists
    operations = list(map((lambda wallet: wallet.operations), wallets))
    # Making flat list
    flat_operations = [op for ops in operations for op in ops]

    income_ops = list(filter((lambda operation: operation.is_income == True), flat_operations))
    income_sum = sum(map((lambda operation: operation.total), income_ops))

    expenses_ops = [op for op in flat_operations if op not in income_ops]
    expenses_sum = sum(map((lambda operation: operation.total), expenses_ops))
    
    context = {
        'balance': balance,
        'wallets': wallets,
        'operations': flat_operations,
        'income_sum': income_sum,
        'expenses_sum': expenses_sum,
    }

    return render_template('dashboard.html', **context)


class CreateWallet(MethodView):
    @login_required
    def get(self):
        form = WalletForm()
        return render_template('create_wallet.html', form=form)


    @login_required
    def post(self):
        form = WalletForm(request.form)
        if form.validate():
            new_wallet = Wallet(
                name=form.name.data,
                pay_type=form.pay_type.data,
                balance=form.balance.data,
                user_id=current_user.id
            )
            db.session.add(new_wallet)
            db.session.commit()
            flash('New wallet created', category='success')
            return redirect(url_for('dashboard'))
        
        return render_template('create_wallet.html', form=form)

app.add_url_rule('/wallet/create', view_func=CreateWallet.as_view('create_wallet'))


class EditWallet(MethodView):
    @login_required
    def get(self, id):
        if legal_wallet(id):
            wallet = Wallet.query.get(id)
            form = WalletForm(
                name=wallet.name,
                pay_type=wallet.pay_type,
                balance=wallet.balance
            )
            context = {
                'wallet': wallet,
                'form': form,
            }
            return render_template('edit_wallet.html', **context)
        
        flash('Wrong wallet', category='danger')
        return redirect(url_for('dashboard'))


    @login_required
    def post(self, id):
        if legal_wallet(id):
            wallet = Wallet.query.get(id)
            form = WalletForm(request.form)
            if form.validate():
                
                wallet.name=form.name.data
                wallet.pay_type=form.pay_type.data
                wallet.balance=form.balance.data

                db.session.commit()

                flash('Wallet updated', category='success')
                return redirect(url_for('dashboard'))
            
            context = {
                'wallet': wallet,
                'form': form,
            }

            return render_template('edit_wallet.html', **context)
            
        flash('Wrong wallet', category='danger')
        return redirect(url_for('dashboard'))

app.add_url_rule('/wallet/edit/<int:id>', view_func=EditWallet.as_view('edit_wallet'))


if __name__ == '__main__':
    app.run(debug=True)