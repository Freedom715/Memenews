import datetime
import os
from random import choice

import requests
from flask import Flask, render_template, redirect, request, make_response, session, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from flask_wtf import FlaskForm
from sqlalchemy import or_
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

import news_resources
from analize import analyze_image_meme, analyze_image_dog, analyze_image_lion
from data import db_session
from data.albums import Album
from data.messages import Message
from data.news import News
from data.users import User
from functions import check_password

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
login_manager = LoginManager()
login_manager.init_app(app)


class BaseForm(FlaskForm):
    background = ""
    text_color = 'white'
    back = '#0a0a0a'
    back_color = 'black'
    font_white = "white"
    js_for_files = ""


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    status = TextAreaField("Немного о себе")
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class NewsForm(FlaskForm):
    title = 'Заголовок'
    content = "Содержание"
    is_private = "Личное"
    submit = 'Применить'


class ProfileForm(FlaskForm):
    name = 'User'
    user = current_user
    cur_user = current_user
    friends = [current_user]
    error = ''


class UsersForm(FlaskForm):
    find_string = StringField('Поиск людей')
    submit = SubmitField('Найти')


def choice_name():
    return choice(
        ['Хм... Наша нейросеть думает что эта фотография похожа на ',
         'Это фото похоже на *барабанная дробь* ',
         'Мы и подумать не могли что существует вещь похожая на ',
         'Очень малый процент людей похожи на '])


class MemesForm(FlaskForm):
    name = choice_name()


def get_base():
    base = BaseForm()
    if current_user.is_authenticated:
        base.background = current_user.background
        base.text_color = 'white' if not current_user.theme else 'black'
        base.back = '#0a0a0a' if not current_user.theme else '#f5f5f5'
        base.back_color = 'black' if not current_user.theme else 'white'
    else:
        base.background = ""
        base.text_color = 'black'
        base.back = '#0a0a0a'
        base.back_color = 'white'
    base.js_for_files = url_for("static", filename="js/bs-custom-file-input.js")
    return base


@app.route('/add_album', methods=['GET', 'POST'])
@login_required
def add_album():
    form = NewsForm()
    if request.method == "GET":
        return render_template('add_album.html', title='Добавление альбома', form=form,
                               base=get_base())
    elif request.method == "POST":
        if form.validate_on_submit():
            session = db_session.create_session()
            album = Album()
            album.name = request.form.get("title")
            album.content = request.form.get("content")
            album.is_private = request.form.get("private")
            f = request.files.get("images")
            if f:
                filename = secure_filename(f.filename)
                f.save("static/img/photos/covers/" + filename)
                album.cover = url_for("static", filename=f"img/photos/covers/{filename}")
                album.photos = url_for("static", filename=f"img/photos/covers/{filename}")
            else:
                album.cover = '/static/img/photos/sample_covers/{}.png'.format(
                    choice(['ololo', 'trollface', 'i_dont_now', 'aaaaa']))
                album.photos = ''
            session.add(album)
            user = session.query(User).filter(User.id == current_user.id).first()
            user.albums = user.albums.rstrip("'") + ', ' + str(album.id) + "'"
            session.commit()
            return redirect('/')
    return render_template('add_album.html', title='Добавление альбома', form=form, base=get_base())


@app.route('/messages/<user_id>', methods=['GET', 'POST'])
@login_required
def messenger(user_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if request.method == "GET":
        messages = session.query(Message).filter(or_(Message.user_from_id == current_user.id,
                                                     Message.user_to == current_user.id))
        return render_template('messenger.html', base=get_base(), messages=messages, user=user)
    elif request.method == "POST":
        messages = session.query(Message).filter(or_(Message.user_from_id == current_user.id,
                                                     Message.user_to == current_user.id))
        text = request.form.get("text")
        message = Message()
        message.text = text
        message.user_from_id = current_user.id
        message.user_to = session.query(User).filter(User.id == user_id).first().id
        session.add(message)
        session.commit()
        return render_template('messenger.html', base=get_base(), messages=messages, user=user)


@app.route('/messages')
@login_required
def messages():
    session = db_session.create_session()
    messages = session.query(Message).filter(
        or_(Message.user_from_id == current_user.id, Message.user_to == current_user.id)).all()
    people_id = []
    people = []
    for elem in messages:
        if not (elem.user_to in people_id or elem.user_from_id in people_id):
            if elem.user_to == current_user.id:
                people.append(session.query(User).filter(User.id == elem.user_from_id).first())
                people_id.append(elem.user_from_id)
            else:
                people.append(session.query(User).filter(User.id == elem.user_to).first())
                people_id.append(elem.user_to)
    print(people_id)
    return render_template('messages.html', base=get_base(), people=people)


@app.route('/album/<album_id>')
def album(album_id):
    session = db_session.create_session()
    album = session.query(Album).filter(Album.id == album_id).first()
    photos = album.photos.split(', ')
    return render_template('photos.html', base=get_base(), photos=photos, album=album)


@app.route('/add_friend/<int:user_id>', methods=['GET', 'POST'])
def add_friend(user_id):
    if user_id != current_user.id:
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        if ', ' not in user.friends and current_user.friends == '':
            user.friends = "'" + str(user_id) + "'"
        elif ', ' not in user.friends and current_user.friends != '':
            user.friends = "'" + user.friends.strip("'") + ', ' + str(user_id) + "'"
        else:
            user.friends = user.friends[:-1] + ', ' + str(user_id) + "'"
        session.commit()
    return redirect(f'/profile/{user_id}')


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/settings', methods=["GET", "POST"])
def settings():
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    if request.method == "GET":
        return render_template('settings.html', title='Параметры', base=get_base(),
                               user=user)
    elif request.method == "POST":
        avatar = request.files.get("avatar")
        username = request.form.get("username")
        status = request.form.get("status")
        background = request.files.get("background")
        theme = request.form.get("theme")
        if username:
            user.name = username
        if status:
            user.status = status
        if background:
            f = background
            filename = secure_filename(f.filename)
            print(filename)
            f.save("static/img/backgrounds/" + filename)
            user.background = url_for("static", filename=f"img/backgrounds/{filename}")
        if avatar:
            f = avatar
            filename = secure_filename(f.filename)
            f.save("static/img/avatars/" + filename)
            name = analyze_image_meme("static/img/avatars/" + filename)
            print("Вы очень похожи на", name)
            user.avatar = url_for("static", filename=f"img/avatars/{filename}")
        if theme == "0":
            user.theme = False
            print(user.theme)
        elif theme == "1":
            user.theme = True
            print(user.theme)

        session.commit()
        return redirect(f'/profile/{current_user.id}')


@app.route('/like_post/<news_id>', methods=['POST'])
def like_post(news_id):
    return redirect('/index')


@app.route('/profile/<user_id>')
def get_profile(user_id):
    form = ProfileForm()
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    albums = session.query(Album).filter(Album.id.in_(user.albums.strip("'").split(', ')))
    form.albums = albums
    form.user = user
    friend = '' if user.friends is None else user.friends
    if len(friend) > 0:
        friends = session.query(User).filter(User.id.in_(friend.strip("'").split(', ')))
        form.friends = friends
    else:
        form.friends = []
        form.error = 'Этот пользователь пока одинок. Напиши ему, может подружитесь.'
    return render_template('profile.html', title='Профиль', form=form, albums=albums,
                           base=get_base())


@app.route('/profile')
def return_profile():
    return redirect(f'/profile/{current_user.id}')


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if request.method == "GET":
        return render_template('add_post.html', title='Добавление новости',
                               form=form, base=get_base())
    elif request.method == "POST":
        session = db_session.create_session()
        news = News()
        news.title = request.form.get("title")
        news.content = request.form.get("content")
        news.user_id = current_user.id
        private = request.form.get("private")
        news.is_private = 0 if private is None else 1
        f = request.files.get("images")
        if f:
            print(f)
            filename = secure_filename(f.filename)
            print(filename)
            f.save("static/img/images/" + filename)
            news.image = url_for("static", filename=f"img/images/{filename}")
        session.add(news)
        session.commit()
        return redirect('/')


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            form.title = news.title
            form.content = news.content
            form.is_private = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            news.title = request.form.get("title")
            news.content = request.form.get("content")
            private = request.form.get("private")
            news.is_private = 0 if private is None else 1
            f = request.files.get("images")
            if f:
                print(f)
                filename = secure_filename(f.filename)
                print(filename)
                f.save("static/img/images/" + filename)
                news.image = url_for("static", filename=f"img/images/{filename}")
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_post.html', title='Редактирование новости', form=form,
                           base=get_base())


@app.route("/people", methods=["GET", "POST"])
def get_people():
    form = UsersForm()
    js = url_for("static", filename="js/bs-custom-file-input.js")
    session = db_session.create_session()
    users = session.query(User)
    find_string = request.form.get("find_string")
    if form.validate_on_submit():
        if form.find_string.data:
            users = session.query(User).filter(User.name.like(f'%{find_string}%'))
        else:
            users = session.query(User)
    return render_template("people.html", form=form, users=users, title='Люди', base=get_base(),
                           js=js)


@app.route('/construct/<neuroname>', methods=['GET', 'POST'])
@login_required
def constructor(neuroname):
    dct = {'Abyssinian': 'Абиссинский кот', 'Bengal': 'Бенгальский кот',
           'Birman': 'Бирманская кошка', 'Bombay': 'Бомбей',
           'British_Shorthair': 'Британская Короткошерстная Кошка',
           'Egyptian_Mau': 'Египетский Мау', 'Maine_Coon': 'Мейн-кун',
           'Persian': 'Персидский кот', 'Ragdoll': 'Рэгдолл', 'Russian_Blue': 'Русская Голубая',
           'Siamese': 'Сиамская кошка', 'Sphynx': 'Сфинкс',
           'american_bulldog': 'американский бульдог',
           'american_pit_bull_terrier': 'американский питбультерьер', 'basset_hound': 'Бассет',
           'beagle': 'Бигль', 'boxer': 'боксер', 'chihuahua': 'чихуахуа',
           'english_cocker_spaniel': 'английский кокер-спаниель',
           'english_setter': 'английский сеттер', 'german_shorthaired': 'немецкий курцхаар',
           'great_pyrenees': 'Пиренейская горная собака', 'havanese': 'Гаванский бишон',
           'japanese_chin': 'Японский Хин', 'keeshond': 'Кеесхонд', 'leonberger': 'Леонбергер',
           'miniature_pinscher': 'Миниатюрный пинчер',
           'newfoundland': 'Ньюфауленд', 'pomeranian': 'Померанский шпиц',
           'pug': 'Мопс', 'saint_bernard': 'Сенбернар', 'samoyed': 'Саемод',
           'scottish_terrier': 'Шотландский терьер', 'shiba_inu': 'Сиба-Ину',
           'staffordshire_bull_terrier': 'Стаффордширский бультерьер',
           'wheaten_terrier': 'Ирландский мягкошёрстный пшеничный терьер',
           'yorkshire_terrier': 'Йоркширский терьер', 'bom_bom': 'Дед Бом-бом',
           'bushemi': 'Стив Бушеми и его глаза', 'goblin': 'Дмитрий (Гоблин) Пучков',
           'leopard': 'Леопард', 'lion': 'Лев', 'people': 'обычный человек',
           'pepe': 'лягушонок Пепе', 'sheldon': 'Шелдон Купер (Теория Большого взрыва)',
           'tiger': 'Тигр', 'yoda': 'малыш Йода (Мандалорец)'}
    form = MemesForm()
    path = ["static/img/neuro/pepe.jpg", "static/img/neuro/pepe.jpg"]
    # Здесь нужно внизу картинок выводить их описание, мол Ты похож на того-того
    # Это можно сделать с помощью словаря
    if form.validate_on_submit():
        f = request.files.get("images")
        if f:
            filename = secure_filename(f.filename)
            filepath = "static/img/neuro/user/" + filename
            f.save(filepath)
            path[0] = url_for("static", filename=f"img/neuro/user/{filename}")
    if neuroname == 'meme':
        name = analyze_image_meme(path[0].lstrip('/'))
        print(name)
        path[1] = url_for("static", filename=f"img/neuro/{name[0]}.jpg").lstrip("/")
        name = form.name + dct[name[0]]
    elif neuroname == 'lions':
        name = analyze_image_lion(path[0].lstrip('/'))
        print(name)
        path[1] = url_for("static", filename=f"img/neuro/{name[0]}.jpg").lstrip("/")
    elif neuroname == 'cat_dogs':
        name = analyze_image_dog(path[0].lstrip('/'))
        print(name)
        response = requests.get('https://api.thecatapi.com/v1/images/search')
        json_response = response.json()
        url = json_response[0]['url']
        response = requests.get(url)
        os.remove('static/img/neuro/user/tmpcat.jpg')
        f = open("static/img/neuro/user/tmpcat.jpg", "wb")
        f.write(response.content)
        f.close()
        path[1] = url_for("static", filename="img/neuro/user/tmpcat.jpg").lstrip("/")
    fact = ''
    path = [('/' + i) if not (i.startswith("/")) else i for i in path]
    return render_template("memes.html", title='Коструктор', base=get_base(), path=path, form=form,
                           name=name, fact=fact)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id,
                                      News.user == current_user).first()
    if news:
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        print(user)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form, base=get_base())
    return render_template('login.html', title='Авторизация', form=form, base=get_base())


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if not check_password(form.password.data):
            if form.password.data != form.password_again.data:
                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Пароли не совпадают")
        else:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message=check_password(form.password.data))
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if session.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        album = Album(
            name=form.name.data + ' album',
            cover='/static/img/photos/sample_covers/{}.png'.format(
                choice(['ololo', 'trollface', 'i_dont_now', 'aaaaa']))
        )
        session.add(album)
        user = User(
            name=form.name.data,
            email=form.email.data,
            status=form.status.data,
            albums=album.name
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form, base=get_base())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    session = db_session.create_session()
    if current_user.is_authenticated:
        news = session.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
    else:
        news = session.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news, title='Лента', base=get_base())


@app.route("/cookie_test")
def cookie_test():
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response(f"Вы пришли на эту страницу {visits_count + 1} раз")
        res.set_cookie("visits_count", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response(
            "Вы пришли на эту страницу в первый раз за последние 2 года")
        res.set_cookie("visits_count", '1',
                       max_age=60 * 60 * 24 * 365 * 2)
    return res


@app.route('/session_test/')
def session_test():
    if 'visits_count' in session:
        session['visits_count'] = session.get('visits_count') + 1
        res = make_response(f"Вы пришли на эту страницу {session['visits_count']} раз")
    else:
        session.permanent = True
        session['visits_count'] = 1
        res = make_response(
            "Вы пришли на эту страницу в первый раз за последние 2 года")
    return res


def main():
    db_session.global_init("db/Memenews.sqlite")
    # app.register_blueprint(news_api.blueprint)
    api.add_resource(news_resources.NewsListResource, '/api/v2/news')
    api.add_resource(news_resources.NewsResource, '/api/v2/news/<int:news_id>')
    app.run()


if __name__ == '__main__':
    main()
