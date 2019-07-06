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
    wallets = current_user.get_wallets()
    balance = current_user.get_balance()
    operations = current_user.get_operations()
    income_sum = current_user.get_income_sum()
    expenses_sum = current_user.get_expenses_sum()
    
    context = {
        'balance': balance,
        'wallets': wallets,
        'operations': operations[:10],
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
            wallet = Wallet.query.get_or_404(id)
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
            wallet = Wallet.query.get_or_404(id)
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
    wallet = Wallet.query.get_or_404(id)
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

    wallet = Wallet.query.get_or_404(wallet_id)
    op_type = Type.query.get_or_404(type_id)

    # all user categories
    user_categories = current_user.get_all_categories()
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
def create_category():
    form = CategoryForm(request.form)
    
    # define choices for operation types
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


@app.route('/categories')
@login_required
def categories_list():
    categories = current_user.get_all_categories()
    return render_template('categories_list.html', categories=categories)

@app.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(request.form)

    # define choices for operation types
    c_types = [(c_type.id, c_type.name) for c_type in Type.query.all()]
    form.type_id.choices = c_types
    form.name.data = category.name

    if request.method == 'POST' and form.validate():
        form = CategoryForm(request.form)
        category.name = form.name.data
        category.type_id = form.type_id.data
        db.session.commit()

        flash('Category was updated', category='info')
        return redirect(url_for('categories_list'))

    context = {
        'form': form,
        'category': category
    }
    return render_template('edit_category.html', **context)


@app.route('/category/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    
    flash('Category was deleted', category='info')
    return redirect(url_for('categories_list'))


@app.route('/operations')
@login_required
def operations_list():
    wallets = current_user.get_wallets()
    operations = current_user.get_operations()
    return render_template('operations_list.html', operations=operations)


@app.route('/user/<int:user_id>/operation/edit/<int:op_id>', methods=['GET', 'POST'])
@login_required
def edit_operation(user_id, op_id):
    operation = Operation.query.get_or_404(op_id)

    wallets = current_user.get_wallets()
    operations = current_user.get_operations()
    
    if current_user.id != user_id or operation not in operations:
        flash('Wrong operation', category='info')
        return redirect(url_for('operations_list'))

    
    form = OperationForm(request.form)

    user_categories = current_user.get_all_categories()
    # Categories with current operation type
    categories = [x for x in user_categories if x.cat_type.name == operation.op_type.name]
    # Make list of tuples with choices for WTForm
    category_choices = [(cat.id, cat.name) for cat in categories]

    form.category.choices = category_choices
    form.total.data = operation.total
    form.type_id.data = operation.type_id

    if request.method == 'POST' and form.validate():
        form = OperationForm(request.form)
        if operation.op_type.name == 'expense':
            if operation.total > form.total.data:
                wallet = Wallet.query.get(operation.wallet_id)
                wallet.balance += (operation.total - form.total.data)
            elif operation.total < form.total.data:
                wallet = Wallet.query.get(operation.wallet_id)
                wallet.balance -= (form.total.data - operation.total)
        elif operation.op_type.name == 'income':
            if operation.total > form.total.data:
                wallet = Wallet.query.get(operation.wallet_id)
                wallet.balance -= (operation.total - form.total.data)
            elif operation.total < form.total.data:
                wallet = Wallet.query.get(operation.wallet_id)
                wallet.balance += (form.total.data - operation.total)
            
        operation.total = form.total.data
        operation.category_id = form.category.data
        db.session.commit()
        return redirect(url_for('operations_list'))

    context = {
        'form': form,
        'operation': operation
    }

    return render_template('edit_operation.html', **context)


@app.route('/user/<int:user_id>/operation/delete/<int:op_id>', methods=['POST'])
@login_required
def delete_operation(user_id, op_id):
    operation = Operation.query.get_or_404(op_id)

    wallets = current_user.get_wallets()
    operations = current_user.get_operations()
    
    if current_user.id != user_id or operation not in operations:
        flash('Wrong operation', category='info')
        return redirect(url_for('operations_list'))

    wallet = Wallet.query.get_or_404(operation.wallet_id)
    if operation.op_type.name == 'income':
        wallet.balance -= operation.total
    elif operation.op_type.name == 'expense':
        wallet.balance += operation.total

    db.session.delete(operation)
    db.session.commit()

    flash('Operation deleted', category='info')
    return redirect(url_for('operations_list'))

@app.route('/wallet/<int:id>/transfer/create', methods=['GET', 'POST'])
@login_required
def create_transfer(id):
    wallet = Wallet.query.get(id)
    if not legal_wallet(id):
        flash('Wrong wallet', category='info')
        return redirect(url_for('dashboard'))

    form = TransferForm(request.form)

    all_wallets = current_user.get_wallets()
    choice_wallets = list(filter((lambda w: w != wallet), all_wallets))
    
    form.wallet.choices = [(w.id, w.name) for w in choice_wallets]

    if request.method == 'POST' and form.validate():
        out_transfer = Operation(
            total = form.total.data,
            type_id = 2,
            wallet_id = wallet.id,
            category_id = Category.query.filter(Category.name == 'transfer').filter(Category.type_id == 2).first().id
        )
        in_transfer = Operation(
            total = form.total.data,
            type_id = 1,
            wallet_id = form.wallet.data,
            category_id = Category.query.filter(Category.name == 'transfer').filter(Category.type_id == 1).first().id
        )
        
        db.session.add_all([out_transfer, in_transfer])
        db.session.commit()

        flash('Transfer created', category='success')
        return redirect(url_for('dashboard'))

    context = {
        'wallet': wallet,
        'form': form
    }
    return render_template('create_transfer.html', **context)
    