import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock

from models.intent import Intent
from models.slot_type import SlotType

PIZZASIZE = {
            "thick": ['thick', 'fat'],
            "skinny": ['thin', 'skinny']
        }
VOLUME = {
            "loud": ['loud', 'high'],
            "quiet": ['quiet', 'low']
        }

@pytest.fixture()
def slots_defs():
    """ Generates slots json"""
    return {
        "pizzasize": PIZZASIZE,
        "volume": VOLUME
    }

def test_create_slot_type(slots_defs):
    slots = SlotType.create_slot_types(slots_defs)

    assert len(slots) == 2
    assert slots[0].name == 'pizzasize'
    assert slots[1].name == 'volume'
    assert slots[0].slots == PIZZASIZE
    assert slots[1].slots == VOLUME

def test_create_slot_type_prefix(slots_defs):
    slots = SlotType.create_slot_types(slots_defs, prefix='test')

    assert len(slots) == 2
    assert slots[0].name == 'testpizzasize'
    assert slots[1].name == 'testvolume'
    assert slots[0].slots == PIZZASIZE
    assert slots[1].slots == VOLUME
