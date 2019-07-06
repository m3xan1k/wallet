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

    def get_wallets(self):
        wallets = db.session.query(Wallet).join(User).filter(User.username == self.username).all()
        return wallets

    def get_balance(self):
        wallets = self.get_wallets()
        balance = sum(map((lambda wallet: wallet.balance), wallets))
        return balance

    def get_operations(self):
        wallets = self.get_wallets()
        # List of lists
        operations = list(map((lambda wallet: wallet.operations), wallets))
        # Making flat list
        flat_operations = [op for ops in operations for op in ops]
        # Sort operations descending
        flat_operations.sort(key=lambda x: x.created, reverse=True)

        return flat_operations

    def get_income_sum(self):
        operations = self.get_operations()
        income_ops = list(filter((lambda operation: operation.op_type.name == 'income'), operations))
        # Count sum...
        income_sum = sum(map((lambda operation: operation.total), income_ops))
        return income_sum

    def get_expenses_sum(self):
        operations = self.get_operations()
        expenses_ops = list(filter((lambda operation: operation.op_type.name == 'expense'), operations))
        expenses_sum = sum(map((lambda operation: operation.total), expenses_ops))
        return expenses_sum

    def get_all_categories(self):
        all_categories = db.session.query(Category).join(User).filter(Category.user_id == self.id).all()
        return all_categories

    def __repr__(self):
        return f'<User username: {self.username}>'


class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    pay_type = db.Column(db.String(30), default='cash')
    balance = db.Column(db.DECIMAL, default=Decimal('0.00'))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'))

    operations = db.relationship('Operation', backref='wallet', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def change_balance(self, op_type_id, amount):
        op_type = Type.query.get(op_type_id)

        types = {
            'income': Decimal(amount),
            'expense': Decimal(-amount),
        }

        self.balance += types[op_type.name]


    def __repr__(self):
        return f'<Wallet id: {self.id}, name: {self.name}, user_id: {self.user_id}>'


class Operation(db.Model):
    __tablename__ = 'operations'

    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.DECIMAL, default=Decimal('0.00'))
    type_id = db.Column(db.Integer, db.ForeignKey('types.id'))

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id', onupdate='CASCADE', ondelete='CASCADE'))

    filename = db.Column(db.String(255))
    description = db.Column(db.String(150))

    created = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, total, type_id, wallet_id, category_id=None):
        self.total = total
        self.type_id = type_id
        self.category_id = category_id
        self.wallet_id = wallet_id

        wallet = Wallet.query.get(wallet_id)
        wallet.change_balance(type_id, total)

    def __repr__(self):
        return f'<Operation id: {self.id}, wallet_id: {self.wallet_id}, category: {self.category_id}, total: {self.total}>'



class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), default='Salary')
    type_id = db.Column(db.Integer, db.ForeignKey('types.id'))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'))
    operations = db.relationship('Operation', backref='category', lazy=True)

    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f'<Category id: {self.id}, name: {self.name}, user_id: {self.user_id}>'


class Type(db.Model):
    __tablename__ = 'types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)

    operations = db.relationship('Operation', backref='op_type', lazy=True)
    categories = db.relationship('Category', backref='cat_type', lazy=True)

    def __repr__(self):
        return f'<Type id: {self.id}, name: {self.name}>'

if __name__ == '__main__':
    pass