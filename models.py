from app import db
from datetime import datetime
from decimal import Decimal
from flask_login import UserMixin


# Models
class User(db.Model, UserMixin):
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

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    operations = db.relationship('Operation', backref='wallet', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def change_balance(self, op_type, amount):
        op_types = {
            'income': Decimal(amount),
            'expense': Decimal(-amount),
        }

        self.balance += op_types[op_type]


    def __repr__(self):
        return f'<Wallet id: {self.id}, name: {self.name}, user_id: {self.user_id}>'


class Operation(db.Model):
    __tablename__ = 'operations'

    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.DECIMAL, default=Decimal('0.00'))
    op_type = db.Column(db.String(30), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', onupdate="CASCADE", ondelete="CASCADE"))

    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    created = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, total, op_type, wallet_id, category_id=None):
        self.total = total
        self.op_type = op_type
        self.category_id = category_id
        self.wallet_id = wallet_id

        wallet = Wallet.query.get(wallet_id)
        wallet.change_balance(op_type, total)

    def __repr__(self):
        return f'<Operation id: {self.id}, wallet_id: {self.wallet_id}, category: {self.category_id}, total: {self.total}>'



class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), default='Salary')
    cat_type = db.Column(db.String(30), nullable=False, default='expense')

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    operations = db.relationship('Operation', backref='category', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f'<Category id: {self.id}, name: {self.name}, user_id: {self.user_id}>'


if __name__ == '__main__':
    pass