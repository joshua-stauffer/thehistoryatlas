import pytest
import string
import random
from the_history_atlas.apps.writemodel.state_manager.text_processor import TextHasher


@pytest.fixture
def hasher():
    return TextHasher()


@pytest.fixture
def whitespace():
    return "".join(random.choice(string.whitespace) for _ in range(100))


@pytest.fixture
def punctuation():
    return "".join(random.choice(string.punctuation) for _ in range(100))


@pytest.fixture
def unicode_chars():
    return "".join(chr(n) for n in range(2**16))


def test_preprocess_text_removes_whitespace(hasher, whitespace):
    assert len(whitespace) == 100
    res = hasher._preprocess_text(whitespace)
    assert res == ""


def test_preprocess_text_removes_punctuation(hasher, punctuation):
    assert len(punctuation) == 100
    res = hasher._preprocess_text(punctuation)
    assert res == ""


def test_preprocess_text_transforms_to_lowercase(hasher):
    assert len(string.ascii_uppercase) == len(string.ascii_lowercase)
    res = hasher._preprocess_text(string.ascii_uppercase)
    assert res == string.ascii_lowercase


def test_preprocess_text_handles_non_ascii_characters(hasher, unicode_chars):

    lowers = []
    uppers = []
    others = []
    for c in unicode_chars:
        if c.islower():
            lowers.append(c)
        elif c.isupper():
            uppers.append(c)
        else:
            others.append(c)
    print(len(lowers), len(uppers), len(others))

    res = hasher._preprocess_text(uppers)
    assert len(res) == len(uppers) + 1  # chr(304), turkish i, turns into a
    # len of two characters! that's interesting..


def test_hash_is_stable(hasher, unicode_chars):
    test_string = "".join(random.choice(unicode_chars) for _ in range(10000))
    hash1 = hasher.get_hash(test_string)
    new_hasher = TextHasher()
    hash2 = new_hasher.get_hash(test_string)
    assert hash1 == hash2
