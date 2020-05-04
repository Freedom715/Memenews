from requests import get
from flask import Flask, request
import requests

from flask_mail import Mail, Message

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'a really really really really long secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:pass@localhost/flask_app_db'
app.config['SECRET_KEY'] = 'a really really really really long secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:pass@localhost/flask_app_db'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'test@gmail.com'  # введите свой адрес электронной почты здесь
app.config['MAIL_DEFAULT_SENDER'] = 'test@gmail.com'  # и здесь
app.config['MAIL_PASSWORD'] = 'password'  # введите пароль


mail = Mail(app)






if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
