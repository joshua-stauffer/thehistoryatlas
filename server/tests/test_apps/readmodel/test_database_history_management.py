def test_database_init(readmodel_db):
    res = readmodel_db.check_database_init()
    assert res == 0


def test_update_last_event_id(readmodel_db):
    readmodel_db.check_database_init()
    readmodel_db.update_last_event_id(11)
    res = readmodel_db.check_database_init()
    assert res == 11
