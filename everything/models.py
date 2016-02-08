from datetime import datetime
from redisorm.core import Persistent, PersistentData
from redisorm.proxy import BooleanProxy, DatetimeProxy, PersistentProxy
import itertools

persistent = Persistent("everything")


class Comment(PersistentData):

    body = Column()
    created_at = Column()
    modified_at = Column()
    voted_users = Column()
    author = Column()
    parent_thread = Column()
    id = Column()

    def __init__(self, body="", voted_users=[], created_at=None, modified_at=None, author=None, parent_thread=None, id=None):
        self.body = body
        self.created_at = created_at or DatetimeProxy(datetime.now())
        self.modified_at = modified_at
        self.voted_users = voted_users
        self.author = PersistentProxy(author)
        self.parent_thread = PersistentProxy(parent_thread)
        self.id = id

    def modify_body(self, body):
        self.body = body
        self.modified_at = DatetimeProxy(datetime.now())

    def vote_count(self):
        return len(self.voted_users)

    def receive_vote_from(self, user):
        self.voted_users.append(user)
        return self.voted_users

    def get_parent_thread(self):
        return self.parent_thread.retrive(Thread, persistent)

    def get_author(self):
        author_id = self.author
        author = None
        if self.author is not None:
            author = persistent.load(User, author_id)
        return author


class User(PersistentData):

    id = Column()
    name = Column()
    screen_name = Column()
    email = Column()
    password = Column()
    created_at = Column()
    logged_in = Column()
    auth_component = Column()
    default_auth_component = None

    def __init__(self, name="", screen_name="", email="", password="", logged_in=False, created_at=None, auth_component=None, id=None):
        self.id = id
        self.name = name
        self.screen_name = screen_name
        self.email = email
        self.password = password
        self.created_at = created_at or DatetimeProxy(datetime.now())
        self.logged_in = BooleanProxy(logged_in)
        self.auth_component = auth_component or User.default_auth_component

    @classmethod
    def set_default_auth_component(cls, auth_component):
        """Set a default auth component to User."""
        cls.default_auth_component = auth_component

    def create_comment(self, thread, body):
        return Comment(parent_thread=PersistentProxy(thread), body=body, author=self)

    def vote_to_comment(self, comment):
        return comment.receive_vote_from(self)

    def is_valid_user(self):
        if not(self.name and self.screen_name and self.email and self.password):
            return False
        return True

    def is_logged_in(self):
        return self.logged_in

    def login(self, password):
        if self.auth_component:
            password = self.auth_component.get_hashed_value(password)

        if self.password == password:
            self.logged_in = True
            return True
        return False

    def before_save(self):
        self.auth_component = None


class Thread(PersistentData):

    id = Column()
    name = Column()
    created_at = Column()
    comments = Column()

    def __init__(self, name="", comments=[], created_at=None, id=None):
        self.id = id
        self.name = name
        self.created_at = created_at or DatetimeProxy(datetime.now())
        self.comments = comments

    def get_comments(self, limit, page):
        comment_ids = persistent.load_all_only_keys(Comment, "id", reverse=True)
        comment_parent_thread_ids = persistent.load_all_only_keys(Comment, "parent_thread", reverse=True)
        all_thread_comments = itertools.zip_longest(comment_ids, comment_parent_thread_ids)

        results = []
        for comment_id, parent_thread_id in all_thread_comments:
            if parent_thread_id == self.id:
                results.append(comment_id)

        for comment_id in itertools.islice(results, limit * (page - 1), limit * page):
            yield persistent.load(Comment, comment_id)

    def add_comment(self, comment):
        pass
