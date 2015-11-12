import hashlib
import operator
import redis
import inspect
import wrapt


class AuthComponent():

    def __init__(self, salt="", hash_method=hashlib.sha256):
        self.salt = salt
        self.hash_method = hash_method

    def get_hashed_value(self, message):
        return self.hash_method((self.salt + message).encode()).hexdigest()
