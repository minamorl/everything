from everything.models import Comment, Thread


def test_init():
    Thread(name=None, comments=[])
