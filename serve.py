from everything.components import AuthComponent, PersistentComponent, PersistentProxy
from everything.models import Thread, Comment, User
import os
import redis
import sys
import functools
from flask import Flask, request, session, jsonify
from datetime import datetime, timedelta
import collections
from functools import reduce

#  redis.StrictRedis().flushall()

save = PersistentComponent().save
load = PersistentComponent().load
load_all = PersistentComponent().load_all
find = PersistentComponent().find

app = Flask(__name__)
app.secret_key = os.environ.get("EVERYTHING_FLASK_SALT")

auth_component = AuthComponent(salt=os.environ.get("EVERYTHING_AUTH_SALT"))
User.set_default_auth_component(auth_component)


def find_user(username):
    user = find(User, lambda x: x.name == username)
    return user


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


@app.route('/api/login.json')
def api_login_get():
    user = find_user(request.args.get('username'))
    r = {"message": "Authentification failed."}
    session.clear()
    if user:
        t = user.login(request.args.get('password'))
        if t is True:
            create_session(user)
            save(user)
            r = {"message": "okay"}
    return jsonify(results=r)


@app.route('/api/logout.json')
def api_logout_get():
    user = find_user(request.args.get('name'))
    r = {"message": "ok"}
    if user:
        user.logged_in = False
        save(user)
    session.clear()
    return jsonify(results=r)


@app.route('/api/thread.json')
def api_thread_get():
    query = request.args.get("q", "")
    thread = find(Thread, lambda x: x.name == query)

    r = collections.deque(maxlen=20)

    if thread is None and query != "":
        return jsonify(results=[])

    if query == "":
        comments = load_all(Comment)
    else:
        comments = thread.get_comments()

    for comment in comments:
        _json = compose_json_from_comment(comment, query)
        r.appendleft(_json)
    return jsonify(results=list(r))


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
    if query == "":
        return jsonify(results={"error"})

    thread = find(Thread, lambda x: x.name == query) or Thread(name=query)
    user = find(User, lambda user: user.name == session.get("user"))
    comment = user.create_comment(thread, body)

    save(thread)
    save(comment)

    return jsonify(results={"message": "ok"})


def create_session(user):
    session['user'] = user.name
    session['user_id'] = user.id
    session['expired_at'] = datetime.now() + timedelta(minutes=100)


@app.route('/api/signup.json')
def signup_api_get():
    if request.args.get('username', "") == "":
        return jsonify(results={"message": "Missing username."})
    if request.args.get('password', "") == "":
        return jsonify(results={"message": "Missing password"})

    user = find_user(request.args.get('username'))
    if user:
        return jsonify(results={"message": "This username is already taken."})

    user = User(name=request.args.get('username'), password=auth_component.get_hashed_value(request.args.get('password')))
    save(user)

    create_session(user)
    return jsonify(results={"message": "okay"})


if __name__ == '__main__':
    app.run(port=9010, debug=True)
