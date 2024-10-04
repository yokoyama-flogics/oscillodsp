import pytest

from qtoscillo import *


def test_find_in_listdict1():
    # listdict is None
    with pytest.raises(TypeError) as err:
        find_in_listdict(None, "name", "foo", "value")
    assert str(err.value) == "'NoneType' object is not iterable"


def test_find_in_listdict2():
    # listdict is an empty list
    with pytest.raises(ValueError) as err:
        find_in_listdict([], "name", "foo", "value")
    assert str(err.value) == "search_key doesn't exist"


def test_find_in_listdict3():
    # search_key doesn't exist
    with pytest.raises(ValueError) as err:
        find_in_listdict(
            [
                {"foo": "apple", "desc": "tasty"},
            ],
            "name",
            "apple",
            "value",
        )
    assert str(err.value) == "search_key doesn't exist"


def test_find_in_listdict4():
    # search_key doesn't match
    assert (
        find_in_listdict(
            [
                {"name": "apple", "desc": "tasty"},
            ],
            "name",
            "banana",
            "value",
        )
        is None
    )


def test_find_in_listdict4a():
    # return_key doesn't exist
    with pytest.raises(ValueError) as err:
        find_in_listdict(
            [
                {"name": "apple", "desc": "tasty"},
            ],
            "name",
            "apple",
            "value",
        )
    assert str(err.value) == "return_key doesn't exist"


def test_find_in_listdict5():
    # value is int
    assert (
        find_in_listdict(
            [
                {"name": 1, "desc": "tasty"},
            ],
            "name",
            1,
            "desc",
        )
        == "tasty"
    )


def test_find_in_listdict6():
    # value is str
    assert (
        find_in_listdict(
            [
                {"name": "apple", "desc": "tasty"},
            ],
            "name",
            "apple",
            "desc",
        )
        == "tasty"
    )


def test_find_in_listdict7():
    # found at the 2nd item
    assert (
        find_in_listdict(
            [
                {"name": "apple", "desc": "tasty"},
                {"name": "banana", "desc": "yellow"},
            ],
            "name",
            "banana",
            "desc",
        )
        == "yellow"
    )


def test_find_in_listdict8():
    # found at the 1st item
    assert (
        find_in_listdict(
            [
                {"name": "apple", "desc": "tasty"},
                {"name": "apple", "desc": "yellow"},
            ],
            "name",
            "apple",
            "desc",
        )
        == "tasty"
    )


def test_trig_status_txt():
    assert trig_status_txt("abc") == "<b>Trigger Status</b>: abc"
