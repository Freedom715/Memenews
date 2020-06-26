from flask import jsonify
from flask_restful import Resource, abort, reqparse

from data import db_session
from data.messages import Message

parser = reqparse.RequestParser()
parser.add_argument("text", required=True)
parser.add_argument("user_to_id", required=True, type=int)
parser.add_argument("user_from_id", required=True, type=int)
parser.add_argument("id", required=True, type=int)
parser.add_argument("time", required=True)


def abort_if_messages_not_found(message_id):
    session = db_session.create_session()
    messages = session.query(Message).get(message_id)
    if not messages:
        abort(404, message=f"Message {message_id} not found")


class MessagesResource(Resource):
    def get(self, message_id):
        abort_if_messages_not_found(message_id)
        session = db_session.create_session()
        messages = session.query(Message).get(message_id)
        return jsonify({"messages": messages.to_dict(
            only=("id", "text", "user_from_id", "user_to_id", "time"))})

    def delete(self, message_id):
        abort_if_messages_not_found(message_id)
        session = db_session.create_session()
        messages = session.query(Message).get(message_id)
        session.delete(messages)
        session.commit()
        return jsonify({"success": "OK"})



class MessagesListResource(Resource):
    def get(self):
        session = db_session.create_session()
        messages = session.query(Message).all()
        return jsonify({"messages": [item.to_dict(
            only=("id", "text", "user_from_id", "user_to_id", "time")) for item in messages]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        message = Message(
            id=args["id"],
            text=args["text"],
            user_from_id=args["user_from_id"],
            user_to_id=args["user_to_id"],
            # is_published=args["is_published"],
            time=args["time"]
        )
        session.add(message)
        session.commit()
        return jsonify({"success": "OK"})
