from everything.components import AuthComponent


def test_init():
    AuthComponent()


def test_get_hashed_value():
    auth = AuthComponent(salt="abcdefg"*7)
    s = "this is test"
    assert s != auth.get_hashed_value(s)
