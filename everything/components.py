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

    def __init__(self, r=None):
        self.r = r or redis.StrictRedis(encoding='utf-8')

    def save(self, obj):
        r = self.r
        classname = obj.__class__.__name__
        params = inspect.signature(obj.__init__).parameters.values()

        obj.before_save()

        for param in params:
            if getattr(obj, param.name) is not None:
                r.hset("everything:{}:{}".format(classname, obj.id), param.name, getattr(obj, param.name))
            else:
                r.hdel("everything:{}:{}".format(classname, obj.id), param.name)

    def load(self, cls, key):
        r = self.r
        classname = cls.__name__

        params = inspect.signature(cls.__init__).parameters.values()
        return cls(**{param.name: r.hget("everything:{}:{}".format(classname, key), param.name) for param in params if param.name != "self"})


class PersistentProxy(wrapt.ObjectProxy):

    @classmethod
    def compose_from_id(cls, kls, key):
        obj = PersistentComponent().load(kls, key)
        return cls(obj)

    def __str__(self):
        return str(self.__wrapped__.id)


class DatetimeProxy(wrapt.ObjectProxy):

    _format = "%Y-%m-%d %H:%M:%s"

    @classmethod
    def compose_from_string(cls, str):
        from datetime import datetime
        obj = datetime.strptime(_format)
        return cls(obj)

    def __str__(self):
        return str(self.__wrapped__.strftime(DatetimeProxy._format))


class BooleanProxy(wrapt.ObjectProxy):

    def __init__(self, wrapped):
        if wrapped == "True" or wrapped is True:
            wrapped = True
        else:
            wrapped = False

        super().__init__(wrapped)
