import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock

from models.bot import Bot
from models.intent import Intent

@pytest.fixture()
def bot_def():
    """ Generates bot json"""
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

def test_create_bot(bot_def):
    bots = Bot.create_bot(bot_def)
    
    assert bots.name == 'name'
    

def test_validate_slot_fails(invalid_bot_defs):
    with pytest.raises(Exception) as excinfo:
        slots = Bot.create_bot(invalid_bot_defs)
        slots[0].validate_slot()

    assert "Utterances missing in slot" in str(excinfo.value)
