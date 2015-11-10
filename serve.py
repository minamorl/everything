from everything.components import AuthComponent, PersistentComponent, PersistentProxy
from everything.models import Thread, Comment, User
import os
import redis
import sys
from flask import Flask, request, session

#  redis.StrictRedis().flushall()

save = PersistentComponent().save
load = PersistentComponent().load
load_all = PersistentComponent().load_all
app = Flask(__name__)
app.secret_key = os.environ.get("EVERYTHING_FLASK_SALT")


def find_user(username):

    user = None
    for _user in load_all(User):
        if (_user.name == username):
            user = _user
    return user


@app.route('/')
def home():

    if session.get('user') is None:
        return "This page is protected. Please login first."

    return "hi, {}".format(session.get('user'))


@app.route('/login')
def login():
    user = find_user(request.args['name'])
    if user:
        session['user'] = user.name
        r = user.login(request.args['password'])
        save(user)
        return "okay"
    else:
        return "Authentification failed."


if __name__ == '__main__':
    app.run(debug=True)
