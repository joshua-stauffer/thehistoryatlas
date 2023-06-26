def test_database_init(db):
    res = db.check_database_init()
    assert res == 0


def test_update_last_event_id(db):
    db.check_database_init()
    db.update_last_event_id(11)
    res = db.check_database_init()
    assert res == 11
