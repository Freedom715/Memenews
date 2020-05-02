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
from data.albums import Photo
from data.messages import Message
from data.news import News
from data.users import User
from functions import check_password, get_time, check_like

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init("db/Memenews.sqlite")
# app.register_blueprint(news_api.blueprint)
api.add_resource(news_resources.NewsListResource, '/api/v2/news')
api.add_resource(news_resources.NewsResource, '/api/v2/news/<int:news_id>')


class BaseForm(FlaskForm):
    background = ""
    text_color = 'white'
    back = '#0a0a0a'
    back_color = '#646464'
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
    password = PasswordField('Пароль', validators=[DataRequired()])


class UsersForm(FlaskForm):
    find_string = StringField('Поиск людей')
    submit = SubmitField('Найти')


def choice_name():
    return choice(
        ['Хм... Наша нейросеть предполагает что на этой фотографии ',
         'Похоже, что на этом фото ',
         "По мнению нейросети на этой картинке "])
    # 'Мы и подумать не могли что существует вещь похожая на '])
    # 'Очень малый процент людей похожи на '])


class MemesForm(FlaskForm):
    name = choice_name()


def create_app():
    return app


def get_base():
    base = BaseForm()
    if current_user.is_authenticated:
        base.background = current_user.background
        base.text_color = 'white' if not current_user.theme else 'black'
        base.back = '#0a0a0a' if not current_user.theme else '#f5f5f5'
        base.back_color = '#1e1e1e' if not current_user.theme else '#969696'
        base.like_image = 'like(dark)' if not current_user.theme else 'like'
    else:
        base.background = ""
        base.text_color = 'black'
        base.back = '#0a0a0a'
        base.back_color = '#969696'
    base.js_for_files = url_for("static", filename="js/bs-custom-file-input.js")
    return base


@app.route('/add_photo', methods=['GET', 'POST'])
@login_required
def add_photo():
    form = NewsForm()
    if request.method == "GET":
        return render_template('add_photo.html', title='Добавление фото', form=form,
                               base=get_base())
    elif request.method == "POST":
        if form.validate_on_submit():
            session = db_session.create_session()
            photo = Photo()
            photo.name = request.form.get("title")
            photo.content = request.form.get("content")
            photo.is_private = request.form.get("private")
            f = request.files.get("images")
            if f:
                filename = secure_filename(f.filename)
                f.save("static/img/photos/covers/" + filename)
                photo.cover = url_for("static", filename=f"img/photos/covers/{filename}")
                photo.photos = url_for("static", filename=f"img/photos/covers/{filename}")
            else:
                photo.cover = '/static/img/photos/sample_covers/{}.png'.format(
                    choice(['ololo', 'trollface', 'i_dont_now', 'aaaaa']))
                photo.photos = ''
            session.add(photo)
            user = session.query(User).filter(User.id == current_user.id).first()
            user.albums = user.albums.rstrip("'") + ', ' + str(photo.id) + "'"
            session.commit()
            return redirect('/')
    return render_template('add_photo.html', title='Добавление фото', form=form, base=get_base())


@app.route('/messages/<user_id>', methods=['GET', 'POST'])
@login_required
def messenger(user_id):
    session = db_session.create_session()
    user_to = session.query(User).filter(User.id == user_id).first()
    if request.method == "GET":
        messages = session.query(Message).filter(or_(Message.user_from_id == current_user.id,
                                                     Message.user_to_id == current_user.id))
        return render_template('messenger.html', base=get_base(), messages=messages, user_to=user_to,
                               get_time=get_time)
    elif request.method == "POST":
        messages = session.query(Message).filter(or_(Message.user_from_id == current_user.id,
                                                     Message.user_to_id == current_user.id))
        text = request.form.get("text")
        message = Message()
        message.text = text
        message.user_from_id = current_user.id
        message.user_to_id = session.query(User).filter(User.id == user_id).first().id
        session.add(message)
        session.commit()
        return render_template('messenger.html', base=get_base(), messages=messages, user_to=user_to,
                               get_time=get_time)


@app.route('/messages')
@login_required
def messages():
    session = db_session.create_session()
    messages = session.query(Message).filter(
        or_(Message.user_from_id == current_user.id, Message.user_to_id == current_user.id)).all()
    people_id = []
    people = []
    for elem in messages:
        if not (elem.user_to_id in people_id or elem.user_from_id in people_id):
            if elem.user_to_id == current_user.id:
                people.append(session.query(User).filter(User.id == elem.user_from_id).first())
                people_id.append(elem.user_from_id)
            else:
                people.append(session.query(User).filter(User.id == elem.user_to_id).first())
                people_id.append(elem.user_to_id)
    return render_template('messages.html', base=get_base(), people=people)


@app.route('/message_delete/<id>', methods=['GET', 'POST'])
@login_required
def message_delete(id):
    session = db_session.create_session()
    message = session.query(Message).filter(Message.id == id,
                                            Message.user_from_id == current_user.id).first()
    if message:
        session.delete(message)
        session.commit()
        return redirect(f'/messages/{message.user_to_id}')
    else:
        abort(404)


@app.route('/photo/<photo_id>')
@login_required
def photo(photo_id):
    session = db_session.create_session()
    photo = session.query(Photo).filter(Photo.id == photo_id).first()
    if photo_id in current_user.albums:
        # Проверка наналичие фотографии в фотографиях пользователя
        # и последующем отображении кнопки удалить
        user = True
    else:
        user = False
    return render_template('photos.html', base=get_base(), photo=photo, user=user)


@app.route('/photo_delete/<photo_id>')
@login_required
def photo_delete(photo_id):
    session = db_session.create_session()
    if photo_id in current_user.albums:
        photo = session.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            session.delete(photo)
        else:
            abort(404)
    else:
        abort(404)
    user = session.query(User).filter(User.id == current_user.id).first()
    user_photo = user.albums.strip("'").split(", ")
    user_photo = list(filter(lambda x: x != photo_id, user_photo))
    user.albums = "'" + ', '.join(user_photo) + "'"
    session.commit()
    return redirect(f'/profile')


@login_required
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


@login_required
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


@app.route('/like_post/<news_id>', methods=['GET', 'POST'])
def like_post(news_id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == news_id).first()
    user = session.query(User).filter(User.id == current_user.id).first()
    lst = user.liked_news
    lst = lst.strip("'")
    if user.liked_news == '':
        user.liked_news = str(news_id)
        news.liked += 1
    elif news_id not in lst.split(', '):
        lst = lst.strip("'") + ', ' + news_id
        print(lst)
        user.liked_news = user.liked_news.rstrip("'") + ', ' + str(news_id) + "'"
        news.liked += 1
    else:
        user = session.query(User).filter(User.id == current_user.id).first()
        user_liked_news = user.liked_news.strip("'").split(", ")
        user_liked_news = list(filter(lambda x: x != news_id, user_liked_news))
        user.liked_news = "'" + ', '.join(user_liked_news) + "'"
        news.liked -= 1
    session.commit()
    return redirect('/')


@app.route('/friend_delete/<friend_id>', methods=['GET', 'POST'])
def friend_delete(friend_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    user_friends = user.friends.strip("'").split(", ")
    user_friends = list(filter(lambda x: x != friend_id, user_friends))
    user.friends = "'" + ', '.join(user_friends) + "'"
    session.commit()
    return redirect('/people')


@app.route('/profile/<user_id>')
def get_profile(user_id):
    form = ProfileForm()
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    photo = session.query(Photo).filter(Photo.id.in_(user.albums.strip("'").split(', '))).all()
    form.photo = photo[:6]
    form.user = user
    friend = '' if user.friends is None else user.friends
    if len(friend) > 0:
        friends = session.query(User).filter(User.id.in_(friend.strip("'").split(', '))).all()
        form.friends = friends[:8]
    else:
        form.friends = []
        form.error = 'Этот пользователь пока одинок. Напиши ему, может подружитесь.'
    return render_template('profile.html', title='Профиль', form=form, photo=photo,
                           base=get_base())


@login_required
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


@login_required
@app.route("/people", methods=["GET", "POST"])
def get_people():
    form = UsersForm()
    js = url_for("static", filename="js/bs-custom-file-input.js")
    session = db_session.create_session()
    users = session.query(User)
    friends = session.query(User).filter(
        User.id.in_(current_user.friends.strip("'").split(', '))).all()
    friends = set(friends)
    find_string = request.form.get("find_string")
    if form.validate_on_submit():
        if form.find_string.data:
            users = session.query(User).filter(User.name.like(f'%{find_string}%')).all()
        else:
            users = session.query(User).all()
    users = set(users)
    users -= friends
    return render_template("people.html", form=form, users=users, title='Люди', base=get_base(),
                           friends=friends,
                           js=js)


@app.route('/neuro/<neuroname>', methods=['GET', 'POST'])
@login_required
def neuro(neuroname):
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
        name = form.name + dct[str(name[0]).split()[0]]
    elif neuroname == 'lions':
        name = analyze_image_lion(path[0].lstrip('/'))
        print(name)
        path[1] = url_for("static", filename=f"img/neuro/{name[0]}.jpg").lstrip("/")
        name = form.name + dct[str(name[0]).split()[0]]
        print(name)
    elif neuroname == 'cat_dogs':
        name = analyze_image_dog(path[0].lstrip('/'))
        print(name)
        name = form.name + dct[str(name[0]).split()[0]]
        print(name)
        response = requests.get('https://api.thecatapi.com/v1/images/search')
        json_response = response.json()
        url = json_response[0]['url']
        response = requests.get(url)
        os.remove('static/img/neuro/user/tmpcat.jpg')
        f = open("static/img/neuro/user/tmpcat.jpg", "wb")
        f.write(response.content)
        f.close()
        path[1] = "static/img/neuro/user/tmpcat.jpg"
    fact = ''
    path = [('/' + i) if not (i.startswith("/")) else i for i in path]
    return render_template("neuro.html", title='Нейросети', base=get_base(), path=path, form=form,
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
                                       message="Пароли не совпадают", base=get_base())
        else:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message=check_password(form.password.data), base=get_base())
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть", base=get_base())
        if session.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть", base=get_base())
        photo = Photo(
            name=form.name.data + ' photo',
            cover='/static/img/photos/sample_covers/{}.png'.format(
                choice(['ololo', 'trollface', 'i_dont_now', 'aaaaa']))
        )
        session.add(photo)
        user = User(
            name=form.name.data,
            email=form.email.data,
            status=form.status.data,
            albums="'" + photo.name + "'",
            friends='',
            theme=1
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form, base=get_base())


@app.route('/user_delete/<int:user_id>', methods=['GET', 'POST'])
def user_delete(user_id):
    session = db_session.create_session()
    form = ProfileForm()
    user = session.query(User).filter(User.id == user_id, user_id == current_user.id).first()
    if request.method == "GET":
        return render_template('user_delete.html', title='Удаление', form=form, base=get_base())
    elif form.validate_on_submit():
        if user.check_password(form.password.data):
            if user:
                user.name = 'DELETE'
                user.status = 'Удалён'
                user.avatar = '/static/img/avatars/no_avatar.png'
                user.albums = ''
                session.commit()
            else:
                abort(404)
        else:
            return render_template('user_delete.html', title='Удаление', form=form, base=get_base(),
                                   message='Пароль неверный')
    return redirect('/logout')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    lst=[]
    session = db_session.create_session()
    if current_user.is_authenticated:
        news = session.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
        lst = current_user.liked_news
        lst = lst.strip("'").split(', ')
    else:
        news = session.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news, title='Лента', base=get_base(),
                           get_time=get_time, lst=lst, check_like=check_like)


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


if __name__ == '__main__':
    app.run()
