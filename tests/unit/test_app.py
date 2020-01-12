"""test_app"""
# pylint: disable=import-error

import mock # pylint: disable=unused-import
import pytest # pylint: disable=unused-import
# pylint: enable=import-error

from pytest_mock import mocker # pylint: disable=unused-import

import app # pylint: disable=import-error
import aws_helper # pylint: disable=import-error,unused-import
from models.intent import Intent
from models.slot_type import SlotType

# pylint: disable=redefined-outer-name
PREFIX = 'pythontest'
BOT_NAME = PREFIX + 'LexBot'
BOT_VERSION = '$LATEST'
LAMBDA_ARN = "arn:aws:lambda:us-east-1:123456789123:function:GreetingLambda"
SLOT_TYPE_NAME = "pizzasize"
DESCRIPTION = "friendly AI chatbot overlord"
SYNONYMS = {
      "thick": ["thick", "fat"],
      'thin': ['thin', 'light']
    }
SLOT_TYPES = {
    "pizzasize": SYNONYMS
}

@pytest.fixture()
def cfn_create_event():
    """ Generates Custom CFN create Event"""
    return cfn_event("Create")

@pytest.fixture()
def cfn_create_no_prefix_event():
    """ Generates Custom CFN create Event"""

    cfn_create_event = cfn_event("Create")
    cfn_create_event['ResourceProperties'].pop('NamePrefix')
    return cfn_create_event


@pytest.fixture()
def cfn_delete_event():
    """ Generates Custom CFN delete Event"""
    return cfn_event("Delete")

def cfn_event(event_type):
    """ Generates Custom CFN Event"""

    # pylint: disable=line-too-long
    return {
        "LogicalResourceId": "LexBot",
        "RequestId": "1234abcd-1234-123a-1ab9-123456bce9dc",
        "RequestType": event_type,
        "ResourceProperties": {
            "name": "LexBot",
            "NamePrefix": PREFIX,
            "ServiceToken": "arn:aws:lambda:us-east-1:123456789123:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
            "loglevel": "info",
            "description": DESCRIPTION,
            "locale": 'en-US',
            'messages': {
                'clarification': 'clarification statement',
                'abortStatement': 'abort statement'
            },
            "intents": [
              {
                  "Name": 'greeting',
                  "CodehookArn": LAMBDA_ARN,
                  "Utterances": ['greetings my friend', 'hello'],
                  "maxAttempts": 3,
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
                    "CodehookArn": LAMBDA_ARN,
                    "Utterances": ['farewell my friend'],
                    "maxAttempts": 3,
                    "Plaintext": {
                        "confirmation": 'a farewell confirmation'
                    }
                }
            ],
            "slotTypes":{
              SLOT_TYPE_NAME: {
                "thick": ["thick", "fat"],
                "thin": ["thin", "light"]
              }
            }
        },
        "ResourceType": "Custom::LexBot",
        "ResponseURL": "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-east-1%3A773592622512%3Astack/elliott-test/db2706d0-2683-11e9-a40a-0a515b01a4a4%7CLexBot%7C23f87176-6197-429a-8fb7-890346bde9dc?AWSAccessKeyId=AKIAJRWMYHFMH4DNUF2Q&Expires=1549075566&Signature=9%2FbjkIyX35f7NRCbdrgIOvbmVes%3D",
        "ServiceToken": "arn:aws:lambda:us-east-1:773592622512:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
        "StackId": "arn:aws:cloudformation:us-east-1:773592622512:stack/python-test/db2706d0-2683-11e9-a40a-0a515b01a4a4"
    }

def _get_bot_response():
    """ Generates get bot response"""

    # pylint: disable=line-too-long
    return {
        "name": "test bot",
        "locale": "en-US",
        "abortStatement": {
            "messages": [
                {
                    "content": "I'm sorry, but I am having trouble understanding. I'm going to pass you over to one of my team mates (they're human!). Please wait to be connected, they will have any information we have discussed.",
                    # "groupNumber": 1
                    "contentType": "PlainText"
                }
            ]
        },
        "clarificationPrompt": {
            "maxAttempts": 1,
            "messages": [
                {
                    "content": "Hmm, I am sorry but I am still learning and I'm not familiar with those words. Could you try again using different words?",
                    "contentType": "PlainText"
                }
            ],
            "responseCard": "string"
        },
        "checksum": "a checksum",
        "childDirected": True,
        "createdDate": 10012019,
        "description": "friendly AI chatbot overlord",

        "failureReason": "a failure",
        "idleSessionTTLInSeconds": 300,
        "status": "READY",
        "version": "$LATEST",

        "intents": [
            {
                "intentName": "string",
                "intentVersion": "string"
            }
        ],
        "lastUpdatedDate": 10012019
    }

@pytest.fixture
def setup(mocker):
    """ setup function """
    context = mock_context(mocker)
    builder = mocker.Mock()
    slot_builder = mocker.Mock()

    return context, builder, slot_builder

def mock_context(mocker):
    """mock_context"""
    context = mocker.Mock()
    context.aws_request_id = 12345
    context.get_remaining_time_in_millis.return_value = 100000.0
    context.invoked_function_arn = \
        'arn:aws:lambda:us-east-1:773592622512:function:elliott-helloworld'
    return context

def _extract_intents(bot_name, resources):
    intents = []
    for json_intent in resources.get('intents'):
      intents.append(Intent.create_intent(bot_name, json_intent))
    return intents

def patch_builder(context, builder, monkeypatch):
    def builder_bot_stub(context): # pylint: disable=unused-argument
        return builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)

def patch_slot_builder(context, slot_builder, monkeypatch):
    def builder_slot_stub(context): # pylint: disable=unused-argument
        return slot_builder

    monkeypatch.setattr(app, "slot_builder_instance", builder_slot_stub)

@mock.patch('models.bot.Bot.create_bot')
@mock.patch('models.intent.Intent.create_intent')
@mock.patch('models.intent.Intent.validate_intent')
def test_create_put_bot_no_prefix(validate_intent, mock_intent, mock_bot, cfn_create_no_prefix_event, setup, monkeypatch):
    """ test_create_puts_bot"""
    context, builder, _ = setup
    resources = cfn_create_no_prefix_event['ResourceProperties']
    messages = resources.get('messages')

    resources.pop('slotTypes')

    mock_bot.return_value = '1234'
    intent = Intent('a', 'b', 'c', 'd', 'e')
    mock_intent.return_value = intent


    builder.put.return_value = {"name": 'LexBot', "version": '$LATEST'}
    patch_builder(context, builder, monkeypatch)

    response = app.create(cfn_create_no_prefix_event, context)
    messages = resources['messages']

    builder.put.assert_called_once_with('1234')
    mock_bot.assert_called_once_with('LexBot',
                                     [intent, intent],
                                     messages,
                                     locale=resources.get('locale'),
                                     description=resources.get('description'))
    validate_intent.assert_called_once
    mock_intent.assert_called

    assert response['BotName'] == 'LexBot'
    assert response['BotVersion'] == BOT_VERSION

def test_create_put_slottypes_no_prefix(cfn_create_no_prefix_event, setup, monkeypatch):
    """ test_create_put_slottypes_no_prefix"""
    context, builder, slot_builder = setup
    builder.put.return_value = {"name": 'LexBot', "version": '$LATEST'}

    slot_types = SlotType.create_slot_types(SLOT_TYPES, prefix='')
    slot_builder.put_slot_type.return_value = {"pizzasize": 'LexBot', "version": '$LATEST'}

    patch_builder(context, builder, monkeypatch)
    patch_slot_builder(context, slot_builder, monkeypatch)

    response = app.create(cfn_create_no_prefix_event, context)
    slot_builder.put_slot_type.assert_called_once_with(slot_types[0])

    assert response['BotName'] == 'LexBot'

@mock.patch('models.bot.Bot.create_bot')
@mock.patch('models.intent.Intent.create_intent')
def test_create_puts(mock_intent, mock_bot, cfn_create_event, setup, monkeypatch):
    """ test_create_puts_bot"""
    context, builder, _ = setup

    cfn_create_event['ResourceProperties'].pop('slotTypes')
    mock_bot.return_value = '1234'

    builder.put.return_value = {"name": BOT_NAME, "version": '$LATEST'}
    intent = Intent('a', 'b', 'c', 'd', None)
    mock_intent.return_value = intent

    patch_builder(context, builder, monkeypatch)

    response = app.create(cfn_create_event, context)

    builder.put.assert_called_once_with('1234')

    assert response['BotName'] == BOT_NAME
    assert response['BotVersion'] == BOT_VERSION

def test_create_put_slottypes(cfn_create_event, setup, monkeypatch):
    """ test_create_put_slottypes_"""
    context, builder, slot_builder = setup

    builder.put.return_value = {"name": BOT_NAME, "version": '$LATEST'}
    slot_types = SlotType.create_slot_types(SLOT_TYPES, prefix=PREFIX)

    slot_builder.put_slot_type.return_value = {"pizzasize": 'LexBot', "version": '$LATEST'}

    patch_builder(context, builder, monkeypatch)
    patch_slot_builder(context, slot_builder, monkeypatch)

    response = app.create(cfn_create_event, context)

    slot_builder.put_slot_type.assert_called_once_with(slot_types[0])
    assert response['BotName'] == BOT_NAME

@mock.patch('models.bot.Bot.create_bot')
@mock.patch('models.intent.Intent.create_intent')
def test_update_puts_no_prefix(mock_intent, mock_bot, cfn_create_no_prefix_event, setup, monkeypatch):
    """ test_update_puts_bot_no_prefix """
    context, builder, _ = setup
    cfn_create_no_prefix_event['ResourceProperties'].pop('slotTypes')
    mock_bot.return_value = '1234'

    builder.put.return_value = {"name": 'LexBot', "version": '$LATEST'}
    intent = Intent('a', 'b', 'c', 'd', None)
    mock_intent.return_value = intent
    patch_builder(context, builder, monkeypatch)

    response = app.update(cfn_create_no_prefix_event, context)

    builder.put.assert_called_once_with('1234')

    assert response['BotName'] == 'LexBot'
    assert response['BotVersion'] == BOT_VERSION

@mock.patch('models.bot.Bot.create_bot')
@mock.patch('models.intent.Intent.create_intent')
def test_update_puts(mock_intent, mock_bot, cfn_create_event, setup, monkeypatch):
    """ test_update_puts_bot"""
    context, builder, _ = setup

    cfn_create_event['ResourceProperties'].pop('slotTypes')
    mock_bot.return_value = '1234'

    builder.put.return_value = {"name": BOT_NAME, "version": '$LATEST'}
    intent = Intent('a', 'b', 'c', 'd', None)
    mock_intent.return_value = intent

    patch_builder(context, builder, monkeypatch)

    response = app.update(cfn_create_event, context)

    builder.put.assert_called_once_with('1234')

    assert response['BotName'] == BOT_NAME
    assert response['BotVersion'] == BOT_VERSION

@pytest.mark.skip(reason="need to work out in CFN what is currently deployed and new")
def test_update_deleted_slot(cfn_create_event, setup, monkeypatch):
    context, _, _ = setup
    app.update(cfn_create_event, context)

@mock.patch('models.bot.Bot.create_bot')
@mock.patch('models.intent.Intent.create_intent')
@mock.patch('models.intent.Intent.validate_intent')
def test_delete(validate_intent, mock_intent, mock_bot, cfn_delete_event, setup, monkeypatch):
    """ test_delete """
    context, builder, slot_builder = setup

    intent = Intent('a', 'b', 'c', 'd', None)
    mock_intent.return_value = intent
    mock_bot.return_value = '1234'

    patch_builder(context, builder, monkeypatch)
    patch_slot_builder(context, slot_builder, monkeypatch)

    app.delete(cfn_delete_event, context)

    builder.delete.assert_called_once_with('1234')

    slot_builder.delete_slot_type.assert_called_once_with(PREFIX + SLOT_TYPE_NAME)


@mock.patch('models.bot.Bot.create_bot')
@mock.patch('models.intent.Intent.create_intent')
@mock.patch('models.intent.Intent.validate_intent')
def test_delete_no_prefix(validate_intent, mock_intent, mock_bot, cfn_delete_event, setup, monkeypatch):
# def test_delete_no_prefix(mock_intent_cls, cfn_delete_event, setup, monkeypatch):
    """ test_delete_no_prefix """
    context, builder, slot_builder = setup
    cfn_delete_event['ResourceProperties'].pop('NamePrefix')
    cfn_delete_event['ResourceProperties']['name'] = 'LexBot'
    intent = Intent('a', 'b', 'c', 'd', 'e')

    mock_intent.return_value = intent
    mock_bot.return_value = '1234'
    patch_builder(context, builder, monkeypatch)
    patch_slot_builder(context, slot_builder, monkeypatch)

    app.delete(cfn_delete_event, context)

    builder.delete.assert_called_once_with('1234')
    slot_builder.delete_slot_type.assert_called_once_with(SLOT_TYPE_NAME)
