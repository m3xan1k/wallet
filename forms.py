from wtforms import Form
from wtforms import StringField, BooleanField, TextAreaField, PasswordField, SelectField, DecimalField, HiddenField
from wtforms.validators import InputRequired, Length, EqualTo, Email, DataRequired
from decimal import Decimal


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


class OperationForm(Form):
    total = DecimalField('Total', default=Decimal('0.00'), validators=[InputRequired()])
    category = SelectField('Category', coerce=int)
    type_id = HiddenField('')


class CategoryForm(Form):
    name = StringField('Category Name', [InputRequired()])
    type_id = SelectField('Type', coerce=int)

class TransferForm(Form):
    total = DecimalField('Total', default=Decimal('0.00'), validators=[InputRequired()])
    wallet = SelectField('Wallet', coerce=int)