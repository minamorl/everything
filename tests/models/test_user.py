from everything.models import User, Comment, Thread


def test_user_init():
    user = User()


def test_is_valid_user():
    assert User(name="a").is_valid_user() == False
    assert User(screen_name="a").is_valid_user() == False
    assert User(name="a", email="a").is_valid_user() == False
    assert User("this", "should", "be", "True").is_valid_user() == True


def test_vote_to_comment():
    user = User("a")
    comment = Comment("dummy")
    assert comment.receive_vote_from(user) == user.vote_to_comment(comment)


def test_is_logged_in():
    user = User(logged_in=True)
    assert user.is_logged_in() == True


def test_login():
    # All paswords must be hashed at real environment.
    password = "password"
    user = User(password=password)

    assert user.is_logged_in() == False
    assert user.login("wrong_password") == False

    assert user.login(password) == True
    assert user.is_logged_in() == True


def test_login_if_passed_hashed():
    from everything.components import AuthComponent

    auth_component = AuthComponent()

    password = "password"
    hashed_password = auth_component.get_hashed_value(password)

    user = User(password=hashed_password)
    user_with_component = User(password=hashed_password, auth_component=auth_component)

    assert user.login(password) == False
    assert user.login(hashed_password) == True

    assert user_with_component.login(password) == True
    assert user_with_component.login(hashed_password) == False

def test_create_comment():
    user = User()
    thread = Thread()
    assert isinstance(user.create_comment(thread, "hogehogehoge"), Comment) == True
