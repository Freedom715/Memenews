import datetime
import os
from random import choice, randint

import requests
from flask import Flask, render_template, redirect, request, make_response, session, url_for, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail
from flask_mail import Message as FlaskMessage
from flask_restful import Api
from flask_wtf import FlaskForm
from sqlalchemy import or_
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

import news_resources
from analize import analyze_image_meme, analyze_image_dog, analyze_image_lion
from data import db_session
from data.messages import Message
from data.news import News
from data.photos import Photo
from data.users import User
from functions import check_password, get_time, check_like

app = Flask(__name__)
api = Api(app)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"
app.config["MAIL_SERVER"] = "smtp.yandex.ru"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "m3menews@yandex.ru"
app.config["MAIL_DEFAULT_SENDER"] = "m3menews@yandex.ru"
app.config["MAIL_PASSWORD"] = "1234567890Memenews"
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init("db/Memenews.sqlite")
# app.register_blueprint(news_api.blueprint)
api.add_resource(news_resources.NewsListResource, "/api/v2/news")
api.add_resource(news_resources.NewsResource, "/api/v2/news/<int:news_id>")

email_confirmation = False
name = ""
email = ""
status = ""
key = ""
password = ""


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
    submit = SubmitField("Отправить проверочное сообщение на указанную почту")
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


def choice_name():
    return choice(
        ["Хм... Наша нейросеть предполагает что на этой фотографии ",
         "Похоже, что на этом фото ",
         "По мнению нейросети на этой картинке "])
    # "Мы и подумать не могли что существует вещь похожая на "])
    # "Очень малый процент людей похожи на "])


class MemesForm(FlaskForm):
    name = choice_name()


def get_base():
    base = BaseForm()
    if current_user.is_authenticated:
        theme = current_user.theme
        if theme == 0 or theme == 1:
            base.background = current_user.background
            base.text_color = "white" if theme == 1 else "black"
            base.back = "#0a0a0a" if theme == 1 else "#f5f5f5"
            base.back_color = "#1e1e1e" if theme == 1 else "#969696"
            base.like_image = "like(dark)" if theme == 1 else "like"
        else:
            if theme == 2:
                base.background = url_for("static", filename="img/backgrounds/fon2.png")
            else:
                base.background = url_for("static", filename="img/backgrounds/fon2_dark.png")
            base.text_color = "white" if theme == 3 else "black"
            base.back = "#0a0a0a" if theme == 3 else "#f5f5f5"
            base.back_color = "#1e1e1e" if theme == 3 else "#969696"
            base.like_image = "like(dark)" if theme == 3 else "like"
    else:
        base.background = ""
        base.text_color = "black"
        base.back = "#0a0a0a"
        base.back_color = "#969696"
    base.js_for_files = url_for("index", filename="js/bs-custom-file-input.js")
    return base


def create_app():
    return app


@app.route("/add_photo", methods=["GET", "POST"])
@login_required
def add_photo():
    form = NewsForm()
    if request.method == "GET":
        return render_template("add_photo.html", title="Добавление фото", form=form,
                               base=get_base())
    elif request.method == "POST":
        if form.validate_on_submit():
            session = db_session.create_session()
            photo = Photo()
            photo.name = request.form.get("title")
            photo.content = request.form.get("content")
            photo.is_private = request.form.get("private")
            photo.user = current_user.id
            f = request.files.get("images")
            if f:
                filename = secure_filename(f.filename)
                f.save("static/img/photos/covers/" + filename)
                photo.cover = url_for("static", filename=f"img/photos/covers/{filename}")
                photo.photos = url_for("static", filename=f"img/photos/covers/{filename}")
            else:
                photo.cover = "/static/img/photos/sample_covers/{}.png".format(
                    choice(["ololo", "trollface", "i_dont_now", "aaaaa"]))
                photo.photos = ""
            session.add(photo)
            user = session.query(User).filter(User.id == current_user.id).first()
            if user.photos:
                if ", " not in user.photos and current_user.photos == "":
                    user.photos = "'" + str(photo.id) + "'"
                elif ", " not in user.photos and current_user.photos != "":
                    user.photos = "'" + user.photos.strip("'") + ", " + str(photo.id) + "'"
                else:
                    user.photos = user.photos.rstrip("'") + ", " + str(photo.id) + "'"
            else:
                user.photos = str(photo.id)
            print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
                  "загрузил фото", photo.name)
            session.commit()
            return redirect("/profile")
    return render_template("add_photo.html", title="Добавление фото", form=form, base=get_base())


@app.route("/messages/<user_id>", methods=["GET", "POST"])
@login_required
def messenger(user_id):
    session = db_session.create_session()
    user_to = session.query(User).filter(User.id == user_id).first()
    if request.method == "GET":
        messages = [elem for elem in session.query(Message).filter(Message.user_from_id == current_user.id,
                                                                   Message.user_to_id == user_id)]
        messages += [elem for elem in session.query(Message).filter(Message.user_to_id == current_user.id,
                                                                    Message.user_from_id == user_id)]

        if not messages == []:
            last = max([elem.id for elem in messages])
        else:
            last = 0
        return render_template(f"messenger.html", base=get_base(), messages=messages, user_to=user_to,
                               get_time=get_time, last=last)
    elif request.method == "POST":
        messages = [elem for elem in session.query(Message).filter(Message.user_from_id == current_user.id,
                                                                   Message.user_to_id == user_id)]
        messages += [elem for elem in session.query(Message).filter(Message.user_to_id == current_user.id,
                                                                    Message.user_from_id == user_id)]

        if not messages == []:
            last = max([elem.id for elem in messages])
        else:
            last = False
        text = request.form.get("text")
        message = Message()
        message.text = text
        message.user_from_id = current_user.id
        message.user_to_id = session.query(User).filter(User.id == user_id).first().id
        session.add(message)
        session.commit()
        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
              "отправил сообщение пользователю",
              session.query(User).filter(User.id == user_id).first().name)
        if last:
            return redirect(f"/messages/{user_id}#{last}")
        else:
            return redirect(f"/messages/{user_id}")


@app.route("/messages")
@login_required
def messages():
    session = db_session.create_session()
    messages = session.query(Message).filter(
        or_(Message.user_from_id == current_user.id, Message.user_to_id == current_user.id)).all()
    people_id = []
    people = []
    # print([elem.id for elem in messages])
    for elem in messages:
        if elem.user_to_id not in people_id:
            people.append(session.query(User).filter(User.id == elem.user_to_id).first())
            people_id.append(elem.user_to_id)
        if elem.user_from_id not in people_id:
            people.append(session.query(User).filter(User.id == elem.user_from_id).first())
            people_id.append(elem.user_from_id)
    return render_template("messages.html", base=get_base(), people_id=people_id,
                           people=people, title="Телеграф")


@app.route("/message_delete/<id>", methods=["GET", "POST"])
@login_required
def message_delete(id):
    session = db_session.create_session()
    message = session.query(Message).filter(Message.id == id,
                                            Message.user_from_id == current_user.id).first()
    messages = session.query(Message).filter(or_(Message.user_from_id == current_user.id,
                                                 Message.user_to_id == current_user.id))
    if messages:
        last = max([elem.id for elem in messages])
    else:
        last = 0
    if message:
        session.delete(message)
        session.commit()
        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
              "удалил сообщение", id)
        return redirect(f"/messages/{message.user_to_id}#{last}")
    else:
        abort(404)


@app.route("/photo/<photo_id>")
def photo(photo_id):
    session = db_session.create_session()
    photo = session.query(Photo).filter(Photo.id == photo_id).first()
    # if photo_id in current_user.photos:
    #     # Проверка наналичие фотографии в фотографиях пользователя
    #     # и последующем отображении кнопки удалить
    #     user = True
    # else:
    #     user = False
    return render_template("photos.html", base=get_base(), photo=photo)


@app.route("/photo_delete/<photo_id>")
@login_required
def photo_delete(photo_id):
    session = db_session.create_session()
    if photo_id in current_user.photos:
        photo = session.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            session.delete(photo)
        else:
            abort(404)
    else:
        abort(404)
    user = session.query(User).filter(User.id == current_user.id).first()
    user_photo = user.photos.strip("'").split(", ")
    user_photo = list(filter(lambda x: x != photo_id, user_photo))
    user.photos = "'" + ", ".join(user_photo) + "'"
    print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "удалил фотографию",
          photo_id)
    session.commit()
    return redirect(f"/profile")


@app.route("/photo_edit/<photo_id>", methods=["GET", "POST"])
def photo_edit(photo_id):
    session = db_session.create_session()
    form = UsersForm()
    photo = session.query(Photo).filter(Photo.id == photo_id).first()
    if request.method == "GET":
        return render_template("photo_edit.html", photo=photo, title="Редактирование фотографии",
                               base=get_base(), form=form)
    if request.method == "POST":
        photo.name = request.form.get("title")
        photo.user = current_user.id
        f = request.files.get("images")
        if f:
            filename = secure_filename(f.filename)
            f.save("static/img/photos/covers/" + filename)
            photo.cover = url_for("static", filename=f"img/photos/covers/{filename}")
            photo.photos = url_for("static", filename=f"img/photos/covers/{filename}")
        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "изменил фото",
              photo.name)
        session.commit()
        return redirect(f"/profile/{current_user.id}")


@login_required
@app.route("/add_friend/<int:user_id>", methods=["GET", "POST"])
def add_friend(user_id):
    if user_id != current_user.id:
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        if ", " not in user.friends and current_user.friends == "":
            user.friends = "'" + str(user_id) + "'"
        elif ", " not in user.friends and current_user.friends != "":
            user.friends = "'" + user.friends.strip("'") + ", " + str(user_id) + "'"
        else:
            user.friends = user.friends[:-1] + ", " + str(user_id) + "'"
        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
              "добавил в друзья", user_id)
        session.commit()
    url_from = request.args.get('url_from')
    return redirect(url_from)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route("/like_post/<news_id>", methods=["GET", "POST"])
def like_post(news_id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == news_id).first()
    user = session.query(User).filter(User.id == current_user.id).first()
    lst = user.liked_news
    if lst:
        lst = str(lst).strip("'")
    if user.liked_news == "":
        user.liked_news = str(news_id)
        news.liked += 1
    elif news_id not in lst.split(", "):
        lst = lst.strip("'") + ", " + news_id
        if ", " not in user.liked_news and current_user.liked_news == "":
            user.liked_news = "'" + str(news_id) + "'"
        elif ", " not in user.liked_news and current_user.liked_news != "":
            user.liked_news = "'" + user.liked_news.strip("'") + ", " + str(news_id) + "'"
        else:
            user.liked_news = user.liked_news.rstrip("'") + ", " + str(news_id) + "'"
        news.liked += 1
    else:
        user = session.query(User).filter(User.id == current_user.id).first()
        user_liked_news = str(user.liked_news).strip("'").split(", ")
        user_liked_news = list(filter(lambda x: x != news_id, user_liked_news))
        user.liked_news = "'" + ", ".join(user_liked_news) + "'"
        news.liked -= 1
    print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "лайкнул пост",
          news_id)
    session.commit()
    return redirect(f"/#{news_id}")


@app.route("/friend_delete/<friend_id>", methods=["GET", "POST"])
def friend_delete(friend_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    user_friends = user.friends.strip("'").split(", ")
    user_friends = list(filter(lambda x: x != friend_id, user_friends))
    user.friends = "'" + ", ".join(user_friends) + "'"
    url_from = request.args.get('url_from')
    print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "удалил друга( ",
          friend_id)
    session.commit()
    return redirect(url_from)


@app.route("/profile/<user_id>")
def get_profile(user_id):
    form = ProfileForm()
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    form.user = user
    if user.photos:
        photo = session.query(Photo).filter(Photo.id.in_(user.photos.strip("'").split(", "))).all()
        form.photo = photo[:6]
    else:
        photo = ""
        form.photo = ""
    friend = "" if user.friends is None else user.friends
    if len(friend) > 0:
        friends = session.query(User).filter(User.id.in_(friend.strip("'").split(", "))).all()
        form.friends = friends[:8]
    else:
        form.friends = []
        form.error = "У этого пользователя еще нет друзей. Напишите ему, может быть вы подружитесь."
    if current_user.is_authenticated:
        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
              "перешел в профиль",
              user.name, user_id)
        friends = session.query(User).filter(
            User.id.in_(current_user.friends.strip("'").split(", "))).all()
        friends_id = [elem.id for elem in friends]
    else:
        friends_id = []
    return render_template("profile.html", title="Профиль", form=form, photo=photo,
                           base=get_base(), friends_id=friends_id)


@login_required
@app.route("/profile")
def return_profile():
    print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
          "перешел в свой профиль")
    return redirect(f"/profile/{current_user.id}")


@app.route("/news", methods=["GET", "POST"])
@login_required
def add_news():
    form = NewsForm()
    if request.method == "GET":
        return render_template("add_post.html", title="Добавление новости",
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
            filename = secure_filename(f.filename)
            f.save("static/img/images/" + filename)
            news.image = url_for("static", filename=f"img/images/{filename}")
        session.add(news)
        session.commit()
        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "создал пост",
              news.title, news.id)
        return redirect("/")


@app.route("/news/<int:id>", methods=["GET", "POST"])
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
            form.image = news.image
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
                filename = secure_filename(f.filename)
                f.save("static/img/images/" + filename)
                news.image = url_for("static", filename=f"img/images/{filename}")
            print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
                  "отредактировал новость", id)
            session.commit()
            return redirect("/")
        else:
            abort(404)
    return render_template("add_post.html", title="Редактирование новости", form=form,
                           base=get_base())


@login_required
@app.route("/people", methods=["GET", "POST"])
def get_people():
    form = UsersForm()
    session = db_session.create_session()
    users = set(session.query(User))
    friends = set(session.query(User).filter(
        User.id.in_(current_user.friends.strip("'").split(", "))).all())
    if form.validate_on_submit():
        find_string = request.form.get("find_string")
        if form.find_string.data:
            users = set(session.query(User).filter(User.name.like(f"%{find_string}%")).all())
            friends = set(session.query(User).filter(
                User.id.in_(current_user.friends.strip("'").split(", "))).filter(
                User.name.like(f"%{find_string}%")).all())
        else:
            users = set(session.query(User).all())
    users -= friends
    return render_template("people.html", form=form, users=users, title="Люди", base=get_base(),
                           friends=friends)


@app.route("/neuro/<neuroname>", methods=["GET", "POST"])
@login_required
def neuro(neuroname):
    dct = {"Abyssinian": "Абиссинский кот", "Bengal": "Бенгальский кот",
           "Birman": "Бирманская кошка", "Bombay": "Бомбей",
           "British_Shorthair": "Британская Короткошерстная Кошка",
           "Egyptian_Mau": "Египетский Мау", "Maine_Coon": "Мейн-кун",
           "Persian": "Персидский кот", "Ragdoll": "Рэгдолл", "Russian_Blue": "Русская Голубая",
           "Siamese": "Сиамская кошка", "Sphynx": "Сфинкс",
           "american_bulldog": "американский бульдог",
           "american_pit_bull_terrier": "американский питбультерьер", "basset_hound": "Бассет",
           "beagle": "Бигль", "boxer": "боксер", "chihuahua": "чихуахуа",
           "english_cocker_spaniel": "английский кокер-спаниель",
           "english_setter": "английский сеттер", "german_shorthaired": "немецкий курцхаар",
           "great_pyrenees": "Пиренейская горная собака", "havanese": "Гаванский бишон",
           "japanese_chin": "Японский Хин", "keeshond": "Кеесхонд", "leonberger": "Леонбергер",
           "miniature_pinscher": "Миниатюрный пинчер",
           "newfoundland": "Ньюфауленд", "pomeranian": "Померанский шпиц",
           "pug": "Мопс", "saint_bernard": "Сенбернар", "samoyed": "Саемод",
           "scottish_terrier": "Шотландский терьер", "shiba_inu": "Сиба-Ину",
           "staffordshire_bull_terrier": "Стаффордширский бультерьер",
           "wheaten_terrier": "Ирландский мягкошёрстный пшеничный терьер",
           "yorkshire_terrier": "Йоркширский терьер", "bom_bom": "Дед Бом-бом",
           "bushemi": "Стив Бушеми и его глаза", "goblin": "Дмитрий (Гоблин) Пучков",
           "leopard": "Леопард", "lion": "Лев", "people": "обычный человек",
           "pepe": "лягушонок Пепе", "sheldon": "Шелдон Купер (Теория Большого взрыва)",
           "tiger": "Тигр", "yoda": "малыш Йода (Мандалорец)"}
    form = MemesForm()
    path = ["static/img/neuro/pepe.jpg", "static/img/neuro/pepe.jpg"]
    if form.validate_on_submit():
        f = request.files.get("images")
        if f:
            filename = secure_filename(f.filename)
            filepath = "static/img/neuro/user/" + filename
            f.save(filepath)
            path[0] = url_for("static", filename=f"img/neuro/user/{filename}")
    if neuroname == "meme":
        name = analyze_image_meme(path[0].lstrip("/"))
        path[1] = url_for("static", filename=f"img/neuro/{name[0]}.jpg").lstrip("/")
        name = form.name + dct[str(name[0]).split()[0]]
    elif neuroname == "lions":
        name = analyze_image_lion(path[0].lstrip("/"))
        path[1] = url_for("static", filename=f"img/neuro/{name[0]}.jpg").lstrip("/")
        name = form.name + dct[str(name[0]).split()[0]]
    elif neuroname == "cat_dogs":
        name = analyze_image_dog(path[0].lstrip("/"))
        name = form.name + dct[str(name[0]).split()[0]]
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        json_response = response.json()
        url = json_response[0]["url"]
        response = requests.get(url)
        os.remove("static/img/neuro/user/tmpcat.jpg")
        f = open("static/img/neuro/user/tmpcat.jpg", "wb")
        f.write(response.content)
        f.close()
        path[1] = "static/img/neuro/user/tmpcat.jpg"
    print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
          "воспользовался нейросетью", neuroname)
    fact = ""
    path = [("/" + i) if not (i.startswith("/")) else i for i in path]
    return render_template("neuro.html", title="Нейросети", base=get_base(), path=path, form=form,
                           name=name, neuroname=neuroname)


@app.route("/news_delete/<int:id>", methods=["GET", "POST"])
@login_required
def news_delete(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id,
                                      News.user == current_user).first()
    news_all = session.query(News).filter(News.user == current_user).all()
    if len(news_all) >= 2:
        redirect_to = news_all[news_all.index(news) - 1].id
    else:
        redirect_to = 0
    if news:
        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "удалил новость",
              news.title, id)
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect(f"/#{redirect_to}")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "вошел")
            return redirect("/")
        return render_template("login.html",
                               message="Неправильный логин или пароль",
                               form=form, base=get_base())
    return render_template("login.html", title="Авторизация", form=form, base=get_base())


@app.route("/password_reset", methods=["GET", "POST"])
@login_required
def password_reset():
    session = db_session.create_session()
    form = PasswordForm()
    url_from = request.args.get('url_from')
    if url_from == '/settings':
        if request.method == "GET":
            return render_template("password_reset.html", base=get_base(), form=form, title="Смена пароля")
        if request.method == "POST":
            if check_password(form.password.data):
                return render_template("password_reset.html", title="Смена пароля",
                                       form=form, message=check_password(form.password.data),
                                       base=get_base())
            if not current_user.check_password(request.form.get("old_password")):
                return render_template("password_reset.html", base=get_base(), form=form,
                                       message="Неверный пароль", title="Смена пароля")
            if form.password.data != form.password_again.data:
                return render_template("password_reset.html", base=get_base(), form=form,
                                       message="Пароли не совпадают", title="Смена пароля")
            print(current_user, form.password.data)
            password = form.password.data
            user = session.query(User).filter(User.id == current_user.id).first()
            user.hashed_password = generate_password_hash(password)
            session.commit()
            return redirect("/settings")


@login_required
@app.route("/settings", methods=["GET", "POST"])
def settings():
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    if request.method == "GET":
        return render_template("settings.html", title="Параметры", base=get_base(),
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
            f.save("static/img/backgrounds/" + filename)
            user.background = url_for("static", filename=f"img/backgrounds/{filename}")
        if avatar:
            f = avatar
            filename = secure_filename(f.filename)
            f.save("static/img/avatars/" + filename)
            name = analyze_image_meme("static/img/avatars/" + filename)
            user.avatar = url_for("static", filename=f"img/avatars/{filename}")
        if theme == "0":
            user.theme = 0
        elif theme == "1":
            user.theme = 1
        elif theme == "2":
            user.theme = 2
        elif theme == "3":
            user.theme = 3

        print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
              "сменил настройки")
        session.commit()
        return redirect(f"/profile/{current_user.id}")


@app.route("/register", methods=["GET", "POST"])
def register():
    global email_confirmation, name, email, status, key, password
    form = RegisterForm()
    cancel = request.args.get("cancel")
    if cancel:
        email_confirmation = False
    session = db_session.create_session()
    if form.validate_on_submit() and not email_confirmation:
        if not check_password(form.password.data):
            if form.password.data != form.password_again.data:
                return render_template("register.html", title="Регистрация",
                                       form=form,
                                       message="Пароли не совпадают", base=get_base())
        else:
            return render_template("register.html", title="Регистрация",
                                   form=form,
                                   message=check_password(form.password.data), base=get_base())
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title="Регистрация",
                                   form=form,
                                   message="Такой пользователь уже есть", base=get_base())
        if session.query(User).filter(User.name == form.name.data).first():
            return render_template("register.html", title="Регистрация",
                                   form=form,
                                   message="Такой пользователь уже есть", base=get_base())
        if not form.email.data:
            return render_template("register.html", title="Регистрация",
                                   form=form,
                                   message="Введите электронную почту", base=get_base())
        if not form.name.data:
            return render_template("register.html", title="Регистрация",
                                   form=form,
                                   message="Введите имя пользователя", base=get_base())
        email_confirmation = True
        name = form.name.data
        email = form.email.data
        password = form.password.data
        status = form.status.data
        key = randint(100000, 999999)
        try:
            msg = FlaskMessage("Memenews", recipients=[email])
            msg.html = f"<h2>Код для регистрации на проекте Memenews</h2>\n<p>{key}</p>"
            mail.send(msg)
        except:
            return render_template("register.html", title="Регистрация",
                                   form=form,
                                   message="Произошла неизвестная ошибка, связанная с электронной почтой, "
                                           "проверьте адрес эл. почты или отправьте запрос позже",
                                   base=get_base())
        return render_template("confirm_email.html", title="Регистрация", form=form, base=get_base(),
                               message="")
    elif email_confirmation:
        if str(form.key.data) == str(key):
            user = User(
                name=name,
                email=email,
                status=status,
                friends="",
                theme=2,
                liked_news=""
            )
            user.set_password(password)
            print(datetime.datetime.now(), name, email, "зарегистрировался")
            session.add(user)
            session.commit()
            email_confirmation = False
            return redirect("/login")
        else:
            return render_template("confirm_email.html", title="Регистрация", form=form,
                                   base=get_base(),
                                   message="Коды не совпадают")
    else:
        return render_template("register.html", title="Регистрация", form=form, base=get_base())


@app.route("/user_delete/<int:user_id>", methods=["GET", "POST"])
def delete_user(user_id):
    session = db_session.create_session()
    form = ProfileForm()
    user = session.query(User).filter(User.id == user_id, user_id == current_user.id).first()
    if request.method == "GET":
        return render_template("user_delete.html", title="Удаление", form=form, base=get_base())
    elif form.validate_on_submit():
        if user.check_password(form.password.data):
            if user:
                print(datetime.datetime.now(), current_user.name, "id: ", current_user.id,
                      "молча удалился")
                user.name = "DELETED"
                user.status = "Удалён"
                user.avatar = "/static/img/avatars/no_avatar.png"
                user.photos = ""
                user.email = user.id
                news = session.query(News).filter(News.user_id == user_id).all()
                for elem in news:
                    session.delete(elem)
                session.commit()
            else:
                abort(404)
        else:
            return render_template("user_delete.html", title="Удаление", form=form, base=get_base(),
                                   message="Пароль неверный")
    return redirect("/logout")


@app.route("/logout")
@login_required
def logout():
    print(datetime.datetime.now(), current_user.name, "id: ", current_user.id, "вышел")
    logout_user()
    return redirect("/")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path,
                               'favicon.ico', mimetype='image/ico')

@app.route("/")
def index():
    lst = []
    session = db_session.create_session()
    if current_user.is_authenticated:
        news = session.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
        lst = current_user.liked_news
        if lst:
            lst = str(lst).strip("'").split(", ")
    else:
        news = session.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news, title="Лента", base=get_base(),
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
        res.set_cookie("visits_count", "1",
                       max_age=60 * 60 * 24 * 365 * 2)
    return res


@app.route("/session_test/")
def session_test():
    if "visits_count" in session:
        session["visits_count"] = session.get("visits_count") + 1
        res = make_response(f"Вы пришли на эту страницу {session['visits_count']} раз")
    else:
        session.permanent = True
        session["visits_count"] = 1
        res = make_response(
            "Вы пришли на эту страницу в первый раз за последние 2 года")
    return res


if __name__ == "__main__":
    app.run(debug=True)
