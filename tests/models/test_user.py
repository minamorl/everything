from everything.models import User, Comment


def test_user_init():
    user = User(name=None, screen_name=None, email=None, password=None)


def test_is_valid_user():
    assert User(name="a").is_valid_user() == False
    assert User(screen_name="a").is_valid_user() == False
    assert User(name="a", email="a").is_valid_user() == False
    assert User("this", "should", "be", "True").is_valid_user() == True


def test_vote_to_comment():
    user = User("a")
    comment = Comment("dummy")
    assert comment.receive_vote_from(user) == user.vote_to_comment(comment)
