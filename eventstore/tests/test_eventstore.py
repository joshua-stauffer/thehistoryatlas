from .seed import SYNTHETIC_EVENTS


def test_setup(db):
    assert True


def test_commit_event(db):
    event = SYNTHETIC_EVENTS[0]
    res = db.commit_event(event)
    assert isinstance(res, list)
    for d in res:
        assert isinstance(d, dict)
