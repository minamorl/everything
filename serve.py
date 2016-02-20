from everything.models import Thread, Comment, User
from everything.components import AuthComponent
from redisorm.core import Persistent, PersistentData
import os
import redis
import sys
import functools
from mead.objects import JSONObject, response, Router
from mead.server import Mead
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
def auth(ctx):

    r = {
        "auth": {
            "name": ctx['session'].get('user')
        }
    }
    if ctx['session'].get('user') == "":
        r = {
            "message": "You are not authorized."
        }
    return response(JSONObject({"results":r}))


@router.route('/api/recent.json')
def api_recent(ctx):
    def get_comments(limit, page):
        all_thread_comments = range(get_max_id(Comment), -1, -1)

        results = []
        for comment_id in all_thread_comments:
            results.append(comment_id)

        for comment_id in itertools.islice(results, limit * (page - 1), limit * page):
            yield persistent.load(Comment, comment_id)

    page = ctx["params"].get("page", 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    r = [compose_json_from_comment(ctx, comment, "") for comment in get_comments(MAX_COMMENT_NUM, page)]

    return response(JSONObject({"results": r}))


def compose_json_from_comment(ctx, comment, query):
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
            "name": ctx['session'].get('user')
        }
    }


@router.route('/api/index.json')
def api_thread_list(ctx):

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
def api_login_get(ctx):
    user = find_user(ctx["params"].get('username'))
    r = {"message": "Authentification failed."}
    ctx['session'].clear()
    if user:
        t = user.login(ctx["params"].get('password'))
        if t is True:
            create_session(ctx, user)
            save(user)
            r = {"message": "okay"}
    return response(JSONObject({"results": r}))


@router.route('/api/logout.json')
def api_logout_get(ctx):
    r = {"message": "okay"}
    ctx['session'].clear()
    return response(JSONObject({"results": r}))


@router.route('/api/thread.json')
def api_thread_get(ctx):

    query = ctx["query"].get("q", "")
    page = ctx["query"].get("page", 1)
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
        _json = compose_json_from_comment(ctx, comment, query)
        r.append(_json)

    return response(JSONObject({"results": list(r)}))


def protected(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        error = {"message": "This page is protected. Please login first."}
        ctx = args[0]

        if ctx['session'].get('user') is None or dateutil.parser.parse(ctx['session'].get('expired_at')) < datetime.now():

            response = response(JSONObject({"results": error}))
            return response

        return func(*args, **kwargs)

    return wrapper


@router.route('/api/comment.json', methods=["POST"])
@protected
def api_comment(ctx):
    query = ctx["params"].get("q", "")
    body = ctx["params"].get("body", "")
    if query == "" or body == "":
        return response(JSONObject({"results": {"message": "Thread title and body must be not empty."}}))

    thread = find(Thread, lambda x: x.name == query) or Thread(name=query)
    user = find(User, lambda user: user.name == ctx['session'].get("user"))
    comment = user.create_comment(thread, body)

    save(thread)
    save(comment)

    r = redis.StrictRedis(decode_responses=True)
    r.sadd(":".join([APP_NAME, "ThreadIndex"]), query)
    r.lpush(":".join([APP_NAME, "RecentThread"]), query)

    return response(JSONObject({"results": {"message": "okay"}}))


def create_session(ctx, user):
    ctx['session']['user'] = user.name
    ctx['session']['user_id'] = user.id
    ctx['session']['expired_at'] = str(datetime.now() + timedelta(hours=100))


@router.route('/api/signup.json', methods=["POST"])
def signup_api_get(ctx):
    if ctx["params"].get('username', "") == "":
        return response(JSONObject({"results": {"message": "Missing username."}}))
    if ctx["params"].get('password', "") == "":
        return response(JSONObject({"results": {"message": "Missing password."}}))

    user = find_user(ctx["params"].get('username'))
    if user:
        return response(JSONObject({"results": {"message": "This username is already taken."}}))

    user = User(name=ctx["params"].get('username'), password=auth_component.get_hashed_value(ctx["params"].get('password')))
    save(user)

    create_session(ctx,user)
    return response(JSONObject({"results": {"message": "okay"}}))


if __name__ == '__main__':
    app.serve(port=9010)
