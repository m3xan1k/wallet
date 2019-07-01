from app import db
from datetime import datetime
from decimal import Decimal


# Models
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), unique=True, nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    
    wallets = db.relationship('Wallet', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f'<User username: {self.username}>'


class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    pay_type = db.Column(db.String(30), default='cash')
    balance = db.Column(db.DECIMAL, default=Decimal('0.00'))

    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    operations = db.relationship('Operation', backref='wallet', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f'<Wallet id: {self.id}, name: {self.name}, user_id: {user.id}>'


class Operation(db.Model):
    __tablename__ = 'operations'

    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.DECIMAL, default=Decimal('0.00'))

    category = db.relationship('Category', backref='operations', lazy=True)
    wallet = db.relationship('Wallet', backref='operations', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f'<Operation id: {self.id}, wallet_id: {self.wallet.id}, category: {self.category.id}>'



class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), default='Salary')
    is_income = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref='categories', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f'<Category id: {self.id}, name: {self.name}, user_id: {user.id}>'