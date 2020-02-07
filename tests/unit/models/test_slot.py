# import mock
import pytest
# from pytest_mock import mocker  # pylint: disable=unused-import
# from unittest.mock import Mock  # pylint: disable=unused-import

# from models.intent import Intent
from models.slot import Slot


@pytest.fixture()
def slots_defs():
    """ Generates slots json"""
    return [{
        "Name": "name",
        "Utterances": [
            "I am {name}",
            "My name is {name}"
        ],
        "Type": "AMAZON.Person",
        "Prompt": "Great thanks, please enter your name."
    }]


@pytest.fixture()
def invalid_slots_defs():
    """ Generates invalid slots json"""
    return [{
        "Name": "name",
        "Type": "AMAZON.Person",
        "Prompt": "Great thanks, please enter your name."
    }]


def test_create_slot(slots_defs):
    slots = Slot.create_slots(slots_defs)

    assert slots[0].name == 'name'
    assert slots[0].slot_type == 'AMAZON.Person'
    assert slots[0].prompt == 'Great thanks, please enter your name.'
    assert slots[0].utterances == ['I am {name}', 'My name is {name}']


def test_validate_slot_fails(invalid_slots_defs):
    with pytest.raises(Exception) as excinfo:
        slots = Slot.create_slots(invalid_slots_defs)
        slots[0].validate_slot()

    assert "Utterances missing in slot" in str(excinfo.value)
