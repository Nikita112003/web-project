from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from data import db_session
from data.user import User
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '421b1f57d3e228b7'

login_manager = LoginManager()
login_manager.init_app(app)


class RegisterForm(FlaskForm):
    email = EmailField('Адрес электронной почты', validators=[DataRequired()])
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


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
        # return redirect('/login')
    params = {
        'title': 'Регистрация',
        'form': form,
    }
    return render_template('register.html', **params)


@app.route('/')
def index():
    params = {
        'title': 'Онлайн-магазин'
    }
    return render_template('index.html', **params)


def main():
    db_session.global_init('db/db.sqlite')

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
