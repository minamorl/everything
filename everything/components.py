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


class PersistentComponent():

    def __init__(self, r=None):
        self.r = r or redis.StrictRedis(encoding='utf-8', decode_responses=True)

    def update_id(self, obj):
        classname = obj.__class__.__name__
        if self.r.get("everything:{}:__latest__".format(classname)) is not None:
            obj.id = int(self.r.get("everything:{}:__latest__".format(classname))) + 1
            self.r.set("everything:{}:__latest__".format(classname), obj.id)
        else:
            obj.id = 0
            self.r.set("everything:{}:__latest__".format(classname), "0")
        return obj.id

    def save(self, obj):
        r = self.r
        classname = obj.__class__.__name__
        params = inspect.signature(obj.__init__).parameters.values()
        obj.before_save()

        obj.id = obj.id or self.update_id(obj)

        for param in params:
            if getattr(obj, param.name) is not None:
                r.hset("everything:{}:{}".format(classname, obj.id), param.name, getattr(obj, param.name))
            else:
                r.hdel("everything:{}:{}".format(classname, obj.id), param.name)

        obj.after_save(obj)

    def load(self, cls, key):
        r = self.r
        classname = cls.__name__
        params = inspect.signature(cls.__init__).parameters.values()
        obj = cls(**{param.name: r.hget("everything:{}:{}".format(classname, key), param.name) for param in params if param.name != "self"})
        obj.after_load()
        return obj

    def load_all(self, cls):
        classname = cls.__name__
        max_id = self.r.get("everything:{}:__latest__".format(classname)) or 0 
        for i in range(int(max_id) + 1):
            yield self.load(cls, str(i))


    def find(self, cls, cond):
        for item in self.load_all(cls):
            if cond(item) is True:
                return item
        return None




class PersistentProxy(wrapt.ObjectProxy):

    @classmethod
    def compose_from_id(cls, kls, key):
        obj = PersistentComponent().load(kls, key)
        return cls(obj)

    def __str__(self):
        try:
            return str(self.__wrapped__.id)
        except AttributeError:
            return self.__wrapped__


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
