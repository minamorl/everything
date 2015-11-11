from everything.components import AuthComponent, PersistentComponent, PersistentProxy
from everything.models import Thread, Comment, User
import os
import redis
import sys
import functools
from flask import Flask, request, session, jsonify
from datetime import datetime, timedelta

#  redis.StrictRedis().flushall()

save = PersistentComponent().save
load = PersistentComponent().load
load_all = PersistentComponent().load_all
find = PersistentComponent().find

app = Flask(__name__)
app.secret_key = os.environ.get("EVERYTHING_FLASK_SALT")


def find_user(username):
    user = find(User, lambda x: x.name == username)
    return user


@app.route('/')
def home():

    if session.get('user') is None or session.get('expired_at') < datetime.now():
        return "This page is protected. Please login first."

    return "hi, {}".format(session.get('user'))


def compose_json_from_comment(comment, query):
    return {
        "author": {
            "name": comment.author.name,
            "screen_name": comment.author.screen_name
        },
        "body": comment.body,
        "thread": {
            "name": query,
        }
    }


@app.route('/api/thread.json')
def api_thread_get():
    query = request.args.get("q", "")
    thread = find(Thread, lambda x: x.name == query)

    r = []
    if thread is None:
        return jsonify(results=r)

    comments = thread.get_comments()

    for comment in comments:
        _json = compose_json_from_comment(comment, query)
        r.append(_json)
    r.reverse()
    return jsonify(results=r)


def protected(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        error = {"error": "This page is protected. Please login first."}

        if session.get('user') is None or session.get('expired_at') < datetime.now():

            response = jsonify(results=error)
            response.status_code = 403
            return response

        return func(*args, **kwargs)

    return wrapper


@app.route('/api/comment.json')
@protected
def api_comment():
    query = request.args.get("q", "")
    body = request.args.get("body", "")

    thread = find(Thread, lambda x: x.name == query) or Thread(name=query)
    user = find(User, lambda x: x.id == session.get("user_id"))
    comment = user.create_comment(thread, body)
    save(comment)
    save(thread)

    return jsonify(results={"message": "ok"})


@app.route('/thread')
def thread():
    query = request.args["q"]
    thread = find(Thread, lambda x: x.name == query) or Thread(name=query)
    save(thread)

    comments = thread.get_comments()
    r = ""
    for comment in comments:
        r += comment.author.id + comment.author.name + "> " + comment.body + "  <br>"
    return r


@app.route('/login')
def login():
    user = find_user(request.args['name'])
    if user:
        session['user'] = user.name
        session['user_id'] = user.id
        session['expired_at'] = datetime.now() + timedelta(minutes=100)
        r = user.login(request.args['password'])
        save(user)
        return "okay"
    else:
        return "Authentification failed."


if __name__ == '__main__':
    app.run(debug=True)
