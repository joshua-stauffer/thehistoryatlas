import pytest
from app.state_manager.event_handler import EventHandler
from app.state_manager.handler_errors import UnknownEventTypeError

def test_build():
    eh = EventHandler(None, None)

def test_handle_event(monkeypatch):
    handlers = {
        'CITATION_ADDED': False,
        'META_ADDED': False,
        'PERSON_ADDED': False,
        'PLACE_ADDED': False,
        'TIME_ADDED': False,
        'PERSON_TAGGED': False,
        'PLACE_TAGGED': False,
        'TIME_TAGGED': False,
    }
    assert all(h == False for h in handlers.values())
    eh = EventHandler(None, None)

    # patch the individual methods responsible for handling events

    def mock_citation_added(_):
        handlers['CITATION_ADDED'] = True

    def mock_meta_added(_):
        handlers['META_ADDED'] = True

    def mock_person_added(_):
        handlers['PERSON_ADDED'] = True

    def mock_place_added(_):
        handlers['PLACE_ADDED'] = True

    def mock_time_added(_):
        handlers['TIME_ADDED'] = True

    def mock_time_tagged(_):
        handlers['TIME_TAGGED'] = True

    def mock_person_tagged(_):
        handlers['PERSON_TAGGED'] = True

    def mock_place_tagged(_):
        handlers['PLACE_TAGGED'] = True

    # remap event handlers since the dict in memory is currently pointing
    # to the addresses of the original handlers
    eh._event_handlers = {
            'CITATION_ADDED': mock_citation_added,
            'META_ADDED': mock_meta_added,
            'PERSON_ADDED': mock_person_added,
            'PLACE_ADDED': mock_place_added,
            'TIME_ADDED': mock_time_added,
            'PERSON_TAGGED': mock_person_tagged,
            'PLACE_TAGGED': mock_place_tagged,
            'TIME_TAGGED': mock_time_tagged
    }

    [eh.handle_event({'type': tag, 'body': '_', 'event_id': i+1})
     for i, tag in enumerate(handlers.keys())]

    for val in handlers.values():
        assert val == True

def test_unknown_type_raises_exception():
    eh = EventHandler(None, None)
    with pytest.raises(UnknownEventTypeError):
        eh.handle_event({
            'type': 'DOESNT EXIST',
            'event_id': 1
        })
