from datetime import datetime


class Comment():

    def __init__(self, body=None, voted_users=[], created_at=None, modified_at=None, author=None):
        self.body = body
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at
        self.voted_users = voted_users
        self.author = author

    def modify_body(self, body):
        self.body = body
        self.modified_at = datetime.now()

    def vote_count(self):
        return len(self.voted_users)


class User():

    def __init__(self, name=None, screen_name=None, email=None, password=None):
        self.name = name
        self.screen_name = screen_name
        self.email = email
        self.password = password
