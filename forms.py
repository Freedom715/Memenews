from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from functions import choice_name


class BaseForm(FlaskForm):
    background = ""
    text_color = "white"
    back = "#0a0a0a"
    back_color = "#646464"
    font_white = "white"
    js_for_files = ""
    favicon = ""


class RegisterForm(FlaskForm):
    email = EmailField("Почта")
    password = PasswordField("Пароль")
    password_again = PasswordField("Повторите пароль")
    name = StringField("Имя пользователя")
    status = TextAreaField("Немного о себе")
    submit = SubmitField("Отправить проверочное сообщение")
    submit_email = SubmitField("Зарегистрироваться")
    key = StringField("Введите проверочный код")


class LoginForm(FlaskForm):
    email = EmailField("Почта", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class NewsForm(FlaskForm):
    title = "Заголовок"
    content = "Содержание"
    is_private = "Личное"
    submit = "Применить"


class ProfileForm(FlaskForm):
    name = "User"
    user = current_user
    cur_user = current_user
    friends = [current_user]
    error = ""
    password = PasswordField("Для удаления введите пароль", validators=[DataRequired()])


class UsersForm(FlaskForm):
    find_string = StringField("Поиск людей")
    submit = SubmitField("Найти")


class PasswordForm(FlaskForm):
    old_password = PasswordField("Введите старый пароль", validators=[DataRequired()])
    password = PasswordField("Ввведите новый пароль", validators=[DataRequired()])
    password_again = PasswordField("Повторите новый пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class MemesForm(FlaskForm):
    name = choice_name()
