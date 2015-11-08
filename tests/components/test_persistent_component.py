from everything.components import PersistentComponent
from everything.models import User, Comment, Thread


persistent = PersistentComponent()

def test_save():
    user = User(name="hello", screen_name="hi")
    persistent.save(user, "user01")

def test_load():
    user = persistent.load(User, "user01")
    print(user)


