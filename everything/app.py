from datetime import datetime
class Comment():

    def __init__(self, body=None, voted_users=[], created_at=None, modified_at=None):
        self.body = body
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at
        self.voted_users = voted_users

    def modify_body(self, body):
        self.body = body
        self.modified_at = datetime.now()

    def voted_count(self):
        return len(self.voted_users)
