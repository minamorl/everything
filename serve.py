from everything.models import Thread, Comment, User
from everything.components import AuthComponent
from redisorm.core import Persistent, PersistentData
import os
import redis
import sys
import functools
from mead.objects import JSONObject
from mead import Mead, response, Router
from datetime import datetime, timedelta
import collections
from functools import reduce
import itertools
import dateutil.parser


APP_NAME = "everything"
TOP_MAX_COMMENT_NUM = 100
RECENT_COMMENT_NUM = 20
MAX_COMMENT_NUM = 10

persistent = Persistent(APP_NAME)
save = persistent.save
load = persistent.load
load_all = persistent.load_all
find = persistent.find
get_max_id = persistent.get_max_id


# Start up mead
router = Router()
app = Mead(session_encrypt_key=os.environ.get("EVERYTHING_MEAD_SALT").encode("utf8"), router=router)

auth_component = AuthComponent(salt=os.environ.get("EVERYTHING_AUTH_SALT"))
User.set_default_auth_component(auth_component)


def find_user(username):
    user = find(User, lambda x: x.name == username)
    return user


@router.route('/api/auth.json')
async def auth(ctx):
    params, session = await ctx.params, await ctx.session
    r = {
        "auth": {
            "name": session.get('user')
        }
    }
    if session.get('user') == "":
        r = {
            "message": "You are not authorized."
        }
    return response(JSONObject({"results": r}))


@router.route('/api/recent.json')
async def api_recent(ctx):
    params, session = await ctx.params, await ctx.session

    def get_comments(limit, page):
        all_thread_comments = range(get_max_id(Comment), -1, -1)

        results = []
        for comment_id in all_thread_comments:
            results.append(comment_id)

        for comment_id in itertools.islice(results, limit * (page - 1), limit * page):
            yield persistent.load(Comment, comment_id)

    page = params.get("page", 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    r = [compose_json_from_comment(comment, "") for comment in get_comments(MAX_COMMENT_NUM, page)]

    return response(JSONObject({"results": r}))


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
    }


@router.route('/api/index.json')
async def api_thread_list(ctx):

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

    return response(JSONObject({"results": r}))


@router.route('/api/login.json', methods=["POST"])
async def api_login_get(ctx):
    params, session = await ctx.params, await ctx.session
    user = find_user(params.get('username'))
    r = {"message": "Authentification failed."}
    session.clear()
    if user:
        t = user.login(params.get('password'))
        if t is True:
            create_session(session, user)
            save(user)
            r = {"message": "okay"}
    return response(JSONObject({"results": r}))


@router.route('/api/logout.json')
async def api_logout_get(ctx):
    params, session = await ctx.params, await ctx.session
    session.clear()
    r = {"message": "okay"}
    return response(JSONObject({"results": r}))


@router.route('/api/thread.json')
async def api_thread_get(ctx):

    query = ctx.query.get("q", "")
    page = ctx.query.get("page", 1)
    try:
        page = int(page)
    except ValueError:
        page = 1

    if query == "":
        return response(JSONObject({"results": []}))
    thread = find(Thread, lambda x: x.name == query)

    if thread is None and query != "":
        return response(JSONObject({"results": []}))

    else:
        comments = thread.get_comments(limit=MAX_COMMENT_NUM, page=page)

    r = collections.deque(maxlen=MAX_COMMENT_NUM)

    for comment in comments:
        _json = compose_json_from_comment(comment, query)
        r.append(_json)

    return response(JSONObject({"results": list(r)}))


class UserVerificationError(Exception):
    pass


def verify_login(session):
    error = {"message": "This page is protected. Please login first."}

    if session.get('user') is None or dateutil.parser.parse(session.get('expired_at')) < datetime.now():
        raise UserVerificationError(JSONObject({"results": error}))


@router.route('/api/comment.json', methods=["POST"])
async def api_comment(ctx):
    params = await ctx.params
    session = await ctx.session
    try:
        verify_login(session)
    except UserVerificationError as e:
        return response(e.args[0])

    query = params.get("q", "")
    body = params.get("body", "")
    if query == "" or body == "":
        return response(JSONObject({"results": {"message": "Thread title and body must be not empty."}}))

    thread = find(Thread, lambda x: x.name == query) or Thread(name=query)
    user = find(User, lambda user: user.name == session.get("user"))
    comment = user.create_comment(thread, body)

    save(thread)
    save(comment)

    r = redis.StrictRedis(decode_responses=True)
    r.sadd(":".join([APP_NAME, "ThreadIndex"]), query)
    r.lpush(":".join([APP_NAME, "RecentThread"]), query)

    return response(JSONObject({"results": {"message": "okay"}}))


def create_session(session, user):
    session['user'] = user.name
    session['user_id'] = user.id
    session['expired_at'] = str(datetime.now() + timedelta(hours=100))


class SignupError(Exception):
    pass


def signup_validation(username, password):
    if username == "":
        raise SignupError(JSONObject({"results": {"message": "Missing username."}}))
    if password == "":
        raise SignupError(JSONObject({"results": {"message": "Missing password."}}))
    user = find_user(username)
    if user:
        raise SignupError(JSONObject({"results": {"message": "This username is already taken."}}))


@router.route('/api/signup.json', methods=["POST"])
async def signup_api_get(ctx):
    params, session = await ctx.params, await ctx.session
    username = params.get('username', "")
    password = params.get('password', "")

    try:
        signup_validation(username, password)
    except SignupError as e:
        return response(e.args[0])

    user = User(name=username, password=auth_component.get_hashed_value(password))
    save(user)

    create_session(session, user)
    return response(JSONObject({"results": {"message": "okay"}}))


if __name__ == '__main__':
    app.serve(port=9010)
