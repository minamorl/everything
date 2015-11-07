from everything.models import Comment, Thread


def test_init():
    Thread(name=None, comments=[])


def test_get_comments():
    c1 = Comment()
    th = Thread(name=None, comments=[c1])
    assert th.get_comments() == [c1]
