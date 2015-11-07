from everything.models import Comment

body = "example"
voted_users = ["0001", "0002"]

def test_comment_init():
    comment1 = Comment("a")
    comment2 = Comment("a")
    assert comment1 != comment2

    comment3 = Comment("a", author="hogehoge")

def test_comment_body():
    comment1 = Comment("a")
    assert comment1.body == "a"


def test_comment_modify():
    comment1 = Comment("a")
    comment1.modify_body("b")
    assert comment1.body == "b"
    assert comment1.modified_at is not None


def test_comment_voted_users():
    comment1 = Comment(body, voted_users)
    assert comment1.voted_users == voted_users


def test_comment_vote_count():
    comment1 = Comment(body, voted_users)
    assert comment1.vote_count() == len(voted_users)


def test_receive_vote_from():
    comment1 = Comment(body, voted_users)
    accept = voted_users + ["cccc"]
    comment1.receive_vote_from("cccc")
    assert comment1.voted_users == accept
