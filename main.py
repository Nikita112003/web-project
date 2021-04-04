from flask import abort, Blueprint, Flask, jsonify, redirect, render_template, request
from flask_login import current_user, LoginManager, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import PasswordField, StringField, SubmitField, BooleanField, DecimalField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from data import db_session
from data.user import User
from data.product import Product
import os
import random
from string import ascii_letters, digits

app = Flask(__name__)
app.config['SECRET_KEY'] = '421b1f57d3e228b7'
app.config['UPLOAD_FOLDER'] = '/static/uploads'

blueprint = Blueprint('products_api', __name__, template_folder='templates')

login_manager = LoginManager()
login_manager.init_app(app)


class RegisterForm(FlaskForm):
    email = EmailField('Адрес электронной почты', validators=[DataRequired()])
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Адрес электронной почты', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class AddProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = DecimalField('Цена', validators=[DataRequired()])
    photo = FileField('Фото', validators=[FileRequired(), FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Добавить')


class EditProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = DecimalField('Цена', validators=[DataRequired()])
    submit = SubmitField('Добавить')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            params = {
                'title': 'Регистрация',
                'form': form,
                'message': 'Пароли не совпадают'
            }
            return render_template('register.html', **params)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            params = {
                'title': 'Регистрация',
                'form': form,
                'message': 'Пользователь с такой почтой уже существует'
            }
            return render_template('register.html', **params)
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()

        login_user(user, remember=True)
        return redirect('/')
    params = {
        'title': 'Регистрация',
        'form': form,
    }
    return render_template('register.html', **params)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        params = {
            'title': 'Авторизация',
            'form': form,
            'message': 'Неправильный логин или пароль'
        }
        return render_template('login.html', **params)
    params = {
        'title': 'Авторизация',
        'form': form
    }
    return render_template('login.html', **params)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/profile')
@login_required
def profile():
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.user_id == current_user.id).all()
    params = {
        'title': 'Личный кабинет',
        'products': products
    }
    return render_template('profile.html', **params)


@app.route('/user/<int:user_id>')
def get_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    if not user:
        abort(404)
    products = db_sess.query(Product).filter(Product.user_id == user.id).all()
    params = {
        'title': user.username,
        'user': user,
        'products': products
    }
    return render_template('user.html', **params)


@app.route('/product/<int:product_id>')
def get_product(product_id):
    db_sess = db_session.create_session()
    product = db_sess.query(Product).get(product_id)
    if not product:
        abort(404)
    params = {
        'title': product.name,
        'product': product
    }
    return render_template('product.html', **params)


@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = Product()
        product.name = form.name.data
        product.price = form.price.data
        product.user_id = current_user.id

        file = form.photo.data
        filetype = file.filename.split('.')[-1]
        while True:
            filename = ''.join(random.choices(ascii_letters + digits, k=25)) + f'.{filetype}'
            if not os.path.exists(f'static/uploads/{filename}'):
                break
        product.photo = filename
        file.save(f'static/uploads/{filename}')

        db_sess.add(product)
        db_sess.commit()

        return redirect('/')
    params = {
        'title': 'Добавление товара',
        'form': form
    }
    return render_template('add_product_form.html', **params)


@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    form = EditProductForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        product = db_sess.query(Product).get(product_id)
        if not product:
            abort(404)
        elif product.user_id != current_user.id:
            abort(403)
        else:
            form.name.data = product.name
            form.price.data = product.price
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = db_sess.query(Product).get(product_id)
        if not product:
            abort(404)
        elif product.user_id != current_user.id:
            abort(403)
        else:
            product.name = form.name.data
            product.price = form.price.data

            db_sess.commit()
            return redirect('/profile')
    params = {
        'title': 'Изменение товара',
        'form': form
    }
    return render_template('add_product_form.html', **params)


@app.route('/delete/<int:product_id>', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    db_sess = db_session.create_session()
    product = db_sess.query(Product).get(product_id)
    if not product:
        abort(404)
    if product.user_id != current_user.id:
        abort(403)
    else:
        try:
            os.remove(f'static/uploads/{product.photo}')
        except FileNotFoundError:
            pass
        db_sess.delete(product)
        db_sess.commit()
    return redirect('/profile')


@app.route('/')
def index():
    db_sess = db_session.create_session()
    products = db_sess.query(Product).all()
    params = {
        'title': 'Онлайн-магазин',
        'products': products
    }
    return render_template('index.html', **params)


@blueprint.route('/api/products')
def api_get_products():
    db_sess = db_session.create_session()
    products = db_sess.query(Product).all()
    return jsonify(
        {
            'products': [product.to_dict(only=('id', 'name', 'price', 'user_id')) for product in products]
        }
    )


@blueprint.route('/api/product/<int:product_id>', methods=['GET'])
def api_get_one_product(product_id):
    db_sess = db_session.create_session()
    product = db_sess.query(Product).get(product_id)
    if not product:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'product': product.to_dict(only=('id', 'name', 'price', 'user_id'))
        }
    )


@blueprint.route('/api/user/<int:user_id>', methods=['GET'])
def api_get_products_of_user(user_id):
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.user_id == user_id)
    if not products:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'products': [product.to_dict(only=('id', 'name', 'price')) for product in products]
        }
    )


def main():
    db_session.global_init('db/db.sqlite')
    app.register_blueprint(blueprint)

    app.run()


if __name__ == '__main__':
    main()
