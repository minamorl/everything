from everything.models import Thread, Comment, User
from everything.components import AuthComponent
from redisorm.core import Persistent, PersistentData
import os
import redis
import sys
import functools
from flask import Flask, request, session, jsonify
from datetime import datetime, timedelta
import collections
from functools import reduce
import itertools


APP_NAME = "everything"
TOP_MAX_COMMENT_NUM = 100
RECENT_COMMENT_NUM = 20
MAX_COMMENT_NUM = 10

persistent = Persistent(APP_NAME)
save = persistent.save
load = persistent.load
load_all = persistent.load_all
find = persistent.find

app = Flask(__name__)
app.secret_key = os.environ.get("EVERYTHING_FLASK_SALT")

auth_component = AuthComponent(salt=os.environ.get("EVERYTHING_AUTH_SALT"))
User.set_default_auth_component(auth_component)


def find_user(username):
    user = find(User, lambda x: x.name == username)
    return user


@app.route('/api/auth.json')
def auth():

    r = {
        "auth": {
            "name": session.get('user')
        }
    }
    if session.get('user') == "":
        r = {
            "message": "You are not authorized."
        }
    return jsonify(results=r)


@app.route('/api/recent.json')
def api_recent():
    comments = itertools.islice(load_all(Comment, reverse=True), RECENT_COMMENT_NUM)

    r = [compose_json_from_comment(comment, "") for comment in comments]

    return jsonify(results=r)


def compose_json_from_comment(comment, query):
    try:
        author_name = comment.get_author().name
    except:
        author_name = ""

    try:
        thread_name = comment.get_parent_thread().name
    except:
        thread_name = ""

    return {
        "author": {
            "name": author_name
        },
        "body": comment.body,
        "thread": {
            "name": thread_name
        },
        "auth": {
            "name": session.get('user')
        }
    }


@app.route('/api/index.json')
def api_thread_list():

    r = []
    red = redis.StrictRedis(decode_responses=True)

    recent_titles = red.lrange(":".join([APP_NAME, "RecentThread"]), 0, 500)
    list_title = []

    for title in recent_titles:
        if title not in list_title:
            r.append({
                "title": title
            })
            list_title.append(title)

    return jsonify(results=r)


@app.route('/api/login.json', methods=["POST"])
def api_login_get():
    user = find_user(request.form.get('username'))
    r = {"message": "Authentification failed."}
    session.clear()
    if user:
        t = user.login(request.form.get('password'))
        if t is True:
            create_session(user)
            save(user)
            r = {"message": "okay"}
    return jsonify(results=r)


@app.route('/api/logout.json')
def api_logout_get():
    r = {"message": "okay"}
    session.clear()
    return jsonify(results=r)


@app.route('/api/thread.json')
def api_thread_get():

    query = request.args.get("q", "")
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    if query == "":
        return jsonify(results=[])
    thread = find(Thread, lambda x: x.name == query)

    if thread is None and query != "":
        return jsonify(results=[])

    else:
        comments = thread.get_comments(limit=MAX_COMMENT_NUM ,page=page)

    r = collections.deque(maxlen=MAX_COMMENT_NUM)

    for comment in comments:
        _json = compose_json_from_comment(comment, query)
        r.append(_json)

    return jsonify(results=list(r))


def protected(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        error = {"message": "This page is protected. Please login first."}

        if session.get('user') is None or session.get('expired_at') < datetime.now():

            response = jsonify(results=error)
            return response

        return func(*args, **kwargs)

    return wrapper


@app.route('/api/comment.json', methods=["POST"])
@protected
def api_comment():
    query = request.form.get("q", "")
    body = request.form.get("body", "")
    if query == "" or body == "":
        return jsonify(results={"message": "Thread title and body must be not empty."})

    thread = find(Thread, lambda x: x.name == query) or Thread(name=query)
    user = find(User, lambda user: user.name == session.get("user"))
    comment = user.create_comment(thread, body)

    save(thread)
    save(comment)

    r = redis.StrictRedis(decode_responses=True)
    r.sadd(":".join([APP_NAME, "ThreadIndex"]), query)
    r.lpush(":".join([APP_NAME, "RecentThread"]), query)

    return jsonify(results={"message": "okay"})


def create_session(user):
    session['user'] = user.name
    session['user_id'] = user.id
    session['expired_at'] = datetime.now() + timedelta(hours=100)


@app.route('/api/signup.json', methods=["POST"])
def signup_api_get():
    if request.form.get('username', "") == "":
        return jsonify(results={"message": "Missing username."})
    if request.form.get('password', "") == "":
        return jsonify(results={"message": "Missing password."})

    user = find_user(request.form.get('username'))
    if user:
        return jsonify(results={"message": "This username is already taken."})

    user = User(name=request.form.get('username'), password=auth_component.get_hashed_value(request.form.get('password')))
    save(user)

    create_session(user)
    return jsonify(results={"message": "okay"})


if __name__ == '__main__':
    app.run(port=9010, debug=True)
