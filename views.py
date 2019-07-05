from app import app, db
from models import *
from forms import *
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from passlib.hash import sha256_crypt
from decimal import Decimal
from flask import render_template, request, redirect, url_for, flash
from flask.views import MethodView


# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# Check if someone tries to access another user's wallet 
def legal_wallet(wallet_id):
    wallet = db.session.query(Wallet).join(User).filter(Wallet.user_id == current_user.id).filter(Wallet.id == wallet_id).first()
    return wallet if wallet else None


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
    # Sort operations descending
    flat_operations.sort(key=lambda x: x.created, reverse=True)
    # Filtering operations to see income only
    income_ops = list(filter((lambda operation: operation.op_type.name == 'income'), flat_operations))
    # Count sum...
    income_sum = sum(map((lambda operation: operation.total), income_ops))
    # expense operations are not income operations
    expenses_ops = [op for op in flat_operations if op not in income_ops]
    expenses_sum = sum(map((lambda operation: operation.total), expenses_ops))
    
    context = {
        'balance': balance,
        'wallets': wallets,
        'operations': flat_operations[:10],
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


@app.route('/wallet/delete/<int:id>', methods=['POST'])
def delete_wallet(id):
    wallet = Wallet.query.get(id)
    db.session.delete(wallet)
    db.session.commit()
    
    flash('Wallet deleted', category='info')
    return redirect(url_for('dashboard'))


@app.route(
    '/wallet/<int:wallet_id>/operation/create/type/<int:type_id>',
    methods=['GET', 'POST'])
@login_required
def create_operation(wallet_id, type_id):
    form = OperationForm(request.form)
    wallet = Wallet.query.get(wallet_id)

    op_type = Type.query.get(type_id)
    # all user categories
    user_categories = db.session.query(Category).join(User).filter(Category.user_id == current_user.id).all()
    # Categories with current operation type
    categories = [x for x in user_categories if x.cat_type.name == op_type.name]
    # Make list of tuples with choices for WTForm
    category_choices = [(cat.id, cat.name) for cat in categories]

    form.type_id.data = op_type.id
    form.category.choices = category_choices
    context = {
        'form': form,
        'wallet': wallet,
    }
   
   
    if request.method == 'POST' and form.validate():
        if legal_wallet(wallet_id):
            operation = Operation(
                total=form.total.data,
                type_id=form.type_id.data,
                category_id = form.category.data,
                wallet_id=wallet_id
            )
            db.session.add(operation)
            db.session.commit()

            flash('Operation successfully submitted', category='success')
            return redirect(url_for('dashboard'))

        flash('Illegal operation', category='danger')
        return render_template('create_operation.html', **context)


    return render_template('create_operation.html', **context)


@app.route('/category/create', methods=['GET', 'POST'])
@login_required
def get():
    form = CategoryForm(request.form)
    c_types = [(c_type.id, c_type.name) for c_type in Type.query.all()]
    form.type_id.choices = c_types

    if request.method == 'POST' and form.validate():
        new_category = Category(
            name=form.name.data,
            type_id=form.type_id.data,
            user_id=current_user.id
        )
        db.session.add(new_category)
        db.session.commit()
        
        flash('Category successfully created', category='success')
        return redirect(url_for('dashboard'))

    return render_template('create_category.html', form=form)
