from everything.components import AuthComponent, PersistentComponent, PersistentProxy
from everything.models import Thread, Comment, User
import os
import redis
import sys
from flask import Flask, request, session
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
        session['expired_at'] = datetime.now() + timedelta(minutes=100)
        r = user.login(request.args['password'])
        save(user)
        return "okay"
    else:
        return "Authentification failed."


if __name__ == '__main__':
    app.run(debug=True)
