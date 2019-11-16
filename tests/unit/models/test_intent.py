import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock

from models.intent import Intent
from models.slot import Slot

@pytest.fixture()
def intent_defs():
    """ Generates intents json"""
    return [
        {
            "Name": 'greeting',
            "CodehookArn": 'an:arn',
            "Utterances": ['greetings my friend','hello'],
            "maxAttempts": 5,
            "Plaintext": {
                "confirmation": 'a confirmation'
            },
            "Slots": [
                {
                "Name": "name",
                "Utterances": [
                    "I am {name}",
                    "My name is {name}"
                ],
                "Type": "AMAZON.Person",
                "Prompt": "Great thanks, please enter your name."
                }
            ]
        },
        {
            "Name": 'farewell',
            "CodehookArn": 'an:arn',
            "maxAttempts": 3,
            "Plaintext": {
                "confirmation": 'a farewell confirmation'
            }
        }        
    ]

def test_create_intent(intent_defs):
    intent = Intent.create_intent('botname', intent_defs[0])
    assert intent.bot_name == 'botname'
    assert intent.intent_name == 'greeting'
    assert intent.utterances == ['greetings my friend','hello']    
    assert intent.attrs['max_attempts'] == 5
    assert intent.attrs['plaintext'] == { "confirmation": 'a confirmation' }

@mock.patch('models.slot.Slot.create_validated_slots')
def test_create_intent_slots(create_validate_slots, intent_defs):    
    create_validate_slots.return_value = ['dummy']
    intent = Intent.create_intent('botname', intent_defs[0])
    
    assert intent.slots == ['dummy']

def test_create_intent_default_max_attempts(intent_defs):
    intent_def = intent_defs[0]
    del intent_def['maxAttempts']
    intent = Intent.create_intent('botname', intent_def)
    assert intent.bot_name == 'botname'
    assert intent.intent_name == 'greeting'
    assert intent.utterances == ['greetings my friend','hello']    
    assert intent.attrs['max_attempts'] == 3
    assert intent.attrs['plaintext'] == { "confirmation": 'a confirmation' }

def test_validate_intent_fails(intent_defs):
    with pytest.raises(Exception) as excinfo:
        Intent.create_intent('botname', intent_defs[1]).validate_intent()

    assert "Utterances missing in intents" in str(excinfo.value)
