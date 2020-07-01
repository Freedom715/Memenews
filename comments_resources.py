from flask import jsonify
from flask_restful import Resource, abort, reqparse

from data import db_session
from data.comments import Comment

parser = reqparse.RequestParser()
# parser.add_argument("id", required=True, type=int)
parser.add_argument("text", required=True)
parser.add_argument("user_id", required=True, type=int)
parser.add_argument("news_id", required=True, type=int)


def abort_if_comments_not_found(comment_id):
    session = db_session.create_session()
    messages = session.query(Comment).get(comment_id)
    if not messages:
        abort(404, comment=f"Comment {comment_id} not found")


class CommentsResource(Resource):
    def get(self, comment_id):
        abort_if_comments_not_found(comment_id)
        session = db_session.create_session()
        comment = session.query(Comment).get(comment_id)
        return jsonify({"comment": comment.to_dict(
            only=("id", "news_id", "text", "user_id"))})

    def delete(self, comment_id):
        abort_if_comments_not_found(comment_id)
        session = db_session.create_session()
        messages = session.query(Comment).get(comment_id)
        session.delete(messages)
        session.commit()
        return jsonify({"success": "OK"})


class CommentsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        comment = session.query(Comment).all()
        return jsonify({"comments": [item.to_dict(
            only=("id", "news_id", "text", "user_id")) for item in comment]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        comment = Comment()
        comment.text = args["text"]
        comment.user_id = args["user_id"]
        comment.news_id = args["news_id"]
        session.add(comment)
        session.commit()
        return jsonify({"success": "OK"})
