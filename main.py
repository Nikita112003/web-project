from flask import abort, Flask, redirect, render_template
from flask_login import current_user, LoginManager, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import PasswordField, StringField, SubmitField, BooleanField, DecimalField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from data import db_session
from data.user import User
from data.good import Good
import os
import random
from string import ascii_letters, digits

app = Flask(__name__)
app.config['SECRET_KEY'] = '421b1f57d3e228b7'
app.config['UPLOAD_FOLDER'] = '/static/uploads'

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


class AddGoodForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = DecimalField('Цена', validators=[DataRequired()])
    photo = FileField('Фото', validators=[FileRequired()])
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
    goods = db_sess.query(Good).filter(Good.user_id == current_user.id).all()
    params = {
        'title': 'Личный кабинет',
        'goods': goods
    }
    return render_template('profile.html', **params)


@app.route('/good/<int:good_id>')
def get_good(good_id):
    db_sess = db_session.create_session()
    good = db_sess.query(Good).get(good_id)
    if not good:
        abort(404)
    params = {
        'title': good.name,
        'good': good
    }
    return render_template('good.html', **params)


@app.route('/add_good', methods=['GET', 'POST'])
@login_required
def add_good():
    form = AddGoodForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        good = Good()
        good.name = form.name.data
        good.price = form.price.data
        good.user_id = current_user.id

        file = form.photo.data
        filetype = file.filename.split('.')[-1]
        while True:
            filename = ''.join(random.choices(ascii_letters + digits, k=25)) + f'.{filetype}'
            if not os.path.exists(f'static/uploads/{filename}'):
                break
        good.photo = filename
        file.save(f'static/uploads/{filename}')

        db_sess.add(good)
        db_sess.commit()

        return redirect('/')
    params = {
        'title': 'Добавление товара',
        'form': form
    }
    return render_template('good_form.html', **params)


@app.route('/')
def index():
    db_sess = db_session.create_session()
    goods = db_sess.query(Good).all()
    params = {
        'title': 'Онлайн-магазин',
        'goods': goods
    }
    return render_template('index.html', **params)


def main():
    db_session.global_init('db/db.sqlite')
    app.run()


if __name__ == '__main__':
    main()
