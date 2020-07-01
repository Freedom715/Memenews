from flask import jsonify
from flask_restful import Resource, abort, reqparse
from flask_login import current_user

from data import db_session
from data.users import User
from data.news import News


def abort_if_comments_not_found(news_id):
    session = db_session.create_session()
    messages = session.query(News).get(news_id)
    if not messages:
        abort(404, comment=f"Comment {news_id} not found")


class LikesResource(Resource):
    def get(self, news_id):
        abort_if_comments_not_found(news_id)
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
        session.commit()
        return jsonify({"news": news.to_dict(
            only=("id", "news_id", "text", "user_id", "liked"))})
