from datetime import datetime


class Comment():

    def __init__(self, body=None, voted_users=[], created_at=None, modified_at=None, author=None, parent_thread=None):
        self.body = body
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at
        self.voted_users = voted_users
        self.author = author
        self.parent_thread = parent_thread

    def modify_body(self, body):
        self.body = body
        self.modified_at = datetime.now()

    def vote_count(self):
        return len(self.voted_users)

    def receive_vote_from(self, user):
        self.voted_users.append(user)
        return self.voted_users

    def get_parent_thread(self):
        return self.parent_thread


class User():

    def __init__(self, name=None, screen_name=None, email=None, password=None, logged_in=False, auth_component=None):
        self.name = name
        self.screen_name = screen_name
        self.email = email
        self.password = password
        self.logged_in = logged_in
        self.auth_component = auth_component

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


class Thread():

    def __init__(self, name=None, comments=[]):
        self.name = name
        self.comments = comments

    def get_comments(self):
        return self.comments
