from datetime import datetime
from .components import PersistentComponent, PersistentProxy, DatetimeProxy, BooleanProxy

persistent = PersistentComponent()


class PersistentData():

    def before_save(self):
        pass

    def before_load(self):
        pass

    def after_save(self, obj):
        pass

    def after_load(self):
        return self

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return str(self.id)

class Comment(PersistentData):

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
        return self.parent_thread

    def after_load(self):
        voted_users_list = eval(self.voted_users)
        self.voted_users = []
        for user in voted_users:
            self.voted_users.append(persistent.load(User, user))


class User(PersistentData):

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
        comment = Comment(parent_thread=PersistentProxy(thread), body=body, author=self)
        thread.add_comment(comment)
        return comment

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

    def before_load(self):
        self.auth_component = default_auth_component


class Thread(PersistentData):

    def __init__(self, name=None, comments=[], created_at=None, id=None):
        self.id = id
        self.name = name
        self.comments = comments
        self.created_at = created_at or DatetimeProxy(datetime.now())

    def get_comments(self):
        return self.comments

    def add_comment(self, comment):
        self.comments.append(comment)

    def after_load(self):
        comments_list = eval(self.comments)
        self.comments = []
        for user in comments_list:
            self.comments.append(persistent.load(User, user))
        return self
