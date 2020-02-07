import pytest

from models.bot import Bot


@pytest.fixture()
def bot_properties():
    """ Generates bot json"""
    return {
        "Name": "name",
        "Description": "Desc here"
    }


@pytest.fixture()
def invalid_slots_defs():
    """ Generates invalid slots json"""
    return [{
        "Name": "name",
        "Type": "AMAZON.Person",
        "Prompt": "Great thanks, please enter your name."
    }]


def test_create_bot(bot_properties):
    name = 'test name'
    intents = 'testi intents'
    messages = 'test messages'
    bot = Bot.create_bot(name, intents, messages, **bot_properties)

    assert bot.name == name
    assert bot.intents == intents
    assert bot.messages == messages
    assert bot.attrs == bot_properties
