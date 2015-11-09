import hashlib
import redis
import inspect
import wrapt


class AuthComponent():

    def __init__(self, salt="", hash_method=hashlib.sha256):
        self.salt = salt
        self.hash_method = hash_method

    def get_hashed_value(self, message):
        return self.hash_method((self.salt + message).encode()).hexdigest()


class PersistentComponent():

    def __init__(self):
        pass

    def save(self, obj, key=None):
        r = redis.StrictRedis(encoding='utf-8')

        classname = obj.__class__.__name__
        params = inspect.signature(obj.__init__).parameters.values()
        for param in params:
            r.hset("everything:{}:{}".format(classname, key), param.name, getattr(obj, param.name))

    def load(self, cls, key):
        r = redis.StrictRedis(encoding='utf-8', decode_responses=True)
        classname = cls.__name__

        params = inspect.signature(cls.__init__).parameters.values()
        return cls(**{param.name: r.hget("everything:{}:{}".format(classname, key), param.name) for param in params if param.name != "self"})


class PersistentProxy(wrapt.ObjectProxy):

    def __str__(self):
        return str(self.__wrapped__.id)
