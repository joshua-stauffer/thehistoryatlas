from tackle import __version__, Tackle
import pytest


def test_version():
    assert __version__ == "0.1.0"


def test_create_test_builds_correctly():
    t = Tackle("some_filename.txt")
    assert len(t._tests) == 0
    assert len(t._results.keys()) == 0
    t.create_test(
        test_name="test the test",
        input_routing_key="test key 1",
        output_routing_key="test key 2",
        dataset=None,  # not actually running the test so not a problem
    )
    assert len(t._tests) == 1
    assert len(t._results.keys()) == 1
    assert t._results.get("test the test") != None


def test_file_loader():
    t = Tackle("some_filename.txt")
    data = t.load_data("tests/test_data.json")
    assert data["name"] == "test"
