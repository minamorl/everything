from datetime import datetime
from redisorm.core import Persistent, PersistentData
from redisorm.proxy import BooleanProxy, DatetimeProxy, PersistentProxy

persistent = Persistent("everything")

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
        parent_thread_id = str(self.parent_thread)
        return persistent.load(Thread, parent_thread_id)

    def get_author(self):
        author_id = self.author
        author = None
        if self.author is not None:
            author = persistent.load(User, author_id)
        return author


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

    def __init__(self, name="", comments=[], created_at=None, id=None):
        self.id = id
        self.name = name
        self.created_at = created_at or DatetimeProxy(datetime.now())
        self.comments = comments

    def get_comments(self):
        for comment in persistent.load_all(Comment):
            if comment.get_parent_thread().id == self.id:
                yield persistent.load(Comment, comment.id)
                

    def add_comment(self, comment):
        pass
