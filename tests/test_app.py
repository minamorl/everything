from everything.app import Comment

body = "example"

def test_comment_init():
    comment1 = Comment("a")
    comment2 = Comment("a")
    assert comment1 != comment2


def test_comment_body():
    comment1 = Comment("a")
    assert comment1.body == "a"

def test_comment_modify():
    comment1 = Comment("a")
    comment1.modify_body("b")
    assert comment1.body == "b"
    assert comment1.modified_at != None

def test_comment_voted_users():
    voted_users = ["0001", "0002"]
    comment1 = Comment(body, voted_users)
    assert comment1.voted_users == voted_users

def test_comment_voted_count():
    voted_users = ["0001", "0002"]
    comment1 = Comment(body, voted_users)
    assert len(comment1.voted_users) == len(voted_users)
