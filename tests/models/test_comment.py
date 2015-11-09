from everything.models import Comment, Thread

body = "example"
voted_users = ["0001", "0002"]


def test_init():
    comment = Comment()

def test_modify():
    comment1 = Comment("a")
    comment1.modify_body("b")
    assert comment1.body == "b"
    assert comment1.modified_at is not None


def test_voted_users():
    comment1 = Comment(body, voted_users)
    assert comment1.voted_users == voted_users


def test_vote_count():
    comment1 = Comment(body, voted_users)
    assert comment1.vote_count() == len(voted_users)


def test_receive_vote_from():
    comment1 = Comment(body, voted_users)
    accept = voted_users + ["cccc"]
    comment1.receive_vote_from("cccc")
    assert comment1.voted_users == accept


def test_get_parent_thread():
    parent_thread = Thread()
    comment = Comment(parent_thread=parent_thread)
    assert comment.get_parent_thread() == parent_thread
