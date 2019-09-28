import requests
import botocore.session
from botocore.stub import Stubber, ANY

import mock
import pytest
from pytest_mock import mocker
import app
import crhelper

BOT_NAME = 'pythontestLexBot'
BOT_VERSION = '$LATEST'
LAMBDA_ARN = "arn:aws:lambda:us-east-1:123456789123:function:GreetingLambda"

@pytest.fixture()
def cfn_create_event():
    """ Generates Custom CFN create Event"""
    return cfn_event("Create")


@pytest.fixture()
def cfn_delete_event():
    """ Generates Custom CFN delete Event"""
    return cfn_event("Delete")

def cfn_event(event_type):
    """ Generates Custom CFN Event"""

    return {
        "LogicalResourceId": "LexBot",
        "RequestId": "1234abcd-1234-123a-1ab9-123456bce9dc",
        "RequestType": event_type,
        "ResourceProperties": {
            "NamePrefix": "pythontest",
            "ServiceToken": "arn:aws:lambda:us-east-1:123456789123:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
            "loglevel": "info",
            "description": "friendly AI chatbot overlord",
            "locale": 'en-US',
            'clarification': {
                'message': 'clarification statement'
            },
            'abortStatement': {
                'message': 'abort statement'
            },
            "intents":[
                {
                    "Name": 'greeting',
                    "CodehookArn": LAMBDA_ARN,
                    "Utterances": ['greetings my friend','hello'],
                    "maxAttempts": 3,
                    "Plaintext": {
                        "confirmation": 'a confirmation'
                    }
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
            "slotTypes":[
                {"Name": 'pizzatype', "Values": ['thin', 'thick']}
            ],
            },
        "ResourceType": "Custom::LexBot",
        "ResponseURL": "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-east-1%3A773592622512%3Astack/elliott-test/db2706d0-2683-11e9-a40a-0a515b01a4a4%7CLexBot%7C23f87176-6197-429a-8fb7-890346bde9dc?AWSAccessKeyId=AKIAJRWMYHFMH4DNUF2Q&Expires=1549075566&Signature=9%2FbjkIyX35f7NRCbdrgIOvbmVes%3D",
        "ServiceToken": "arn:aws:lambda:us-east-1:773592622512:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
        "StackId": "arn:aws:cloudformation:us-east-1:773592622512:stack/python-test/db2706d0-2683-11e9-a40a-0a515b01a4a4"
    }

@pytest.fixture()
def get_bot_response():
    return _get_bot_response()

def _get_bot_response():
    """ Generates get bot response"""
    return {
        "name": "test bot",
        "locale": "en-US",
        "abortStatement": {
            "messages": [
                {
                    "content": "I'm sorry, but I am having trouble understanding. I'm going to pass you over to one of my team mates (they're human!). Please wait to be connected, they will have any information we have discussed.",
                    "contentType": "PlainText"
                    # "groupNumber": 1
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


def put_bot_request(bot_name, bot_props, put_bot_response, has_checksum=False):
    """ put bot request """

    put_request = {
        'abortStatement': ANY,
        'childDirected': False,
        'clarificationPrompt': {
            'maxAttempts': 1,
            'messages': [
                {
                    'content': bot_props['clarification']['message'],
                    'contentType': 'PlainText'
                }
            ]
        },
        'description': put_bot_response['description'],
        'idleSessionTTLInSeconds': ANY,
        'name': bot_name,
        'intents': [
            {'intentName': 'greeting', 'intentVersion': '$LATEST'},
            {'intentName': 'farewell', 'intentVersion': '$LATEST'}
        ],
        'locale': put_bot_response['locale'],
        'processBehavior': 'BUILD'
    }

    if(has_checksum):
      put_request.update({
                           'checksum': ANY,
                        })
    return put_request

def get_bot_request():
    """ get bot request """
    return {
        'name': BOT_NAME, 'versionOrAlias': BOT_VERSION}

def put_bot_version_interaction(bot_name, bot_version):
    """ put bot request interaction"""
    create_bot_version_response = {
        'name': bot_name,
        'version': bot_version
    }

    create_bot_version_params = {
        'checksum': 'rnd value',
        'name': bot_name
    }
    return create_bot_version_response, create_bot_version_params

@pytest.fixture
def setup(mocker):
    """ setup function """
    lex = botocore.session.get_session().create_client('lex-models')
    context = mock_context(mocker)
    builder = mocker.Mock()
    slot_builder = mocker.Mock()

    return lex, context, builder, slot_builder

def stub_not_found_get_request(stubber):
    """stub not found get request"""
    stubber.add_client_error('get_bot', http_status_code=404)

def stub_get_request(stubber):
    """stub get request"""
    stubber.add_response('get_bot', _get_bot_response(), get_bot_request())

def put_intent_responses():
    put_intent_response_1 = {'intentName': 'greeting', 'intentVersion': '$LATEST'}
    put_intent_response_2 = {'intentName': 'farewell', 'intentVersion': '$LATEST'}

    return [put_intent_response_1, put_intent_response_2]

def stub_put_intent(intent_builder):
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.put_intent.side_effect = put_intent_responses()
        return intent_builder_instance

def mock_context(mocker):
        context = mocker.Mock()
        context.aws_request_id = 12345
        context.get_remaining_time_in_millis.return_value = 100000.0
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:773592622512:function:elliott-helloworld'
        return context

def test_create_put_bot_no_prefix(cfn_create_event, setup, monkeypatch) :
    """ test_create_puts_bot"""
    lex, context, builder, _ = setup

    cfn_create_event['ResourceProperties'].pop('NamePrefix')
    cfn_create_event['ResourceProperties'].pop('slotTypes')
    cfn_create_event['ResourceProperties']['name'] = 'LexBot'

    builder.put.return_value = {"name": 'LexBot', "version": '$LATEST' }

    def builder_bot_stub(event, context):
        return builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)

    response = app.create(cfn_create_event, context)

    builder.put.assert_called_once_with('LexBot',
            cfn_create_event['ResourceProperties'])

    assert response['BotName'] == 'LexBot'
    assert response['BotVersion'] == BOT_VERSION

def test_create_put_slottypes_no_prefix(cfn_create_event, setup, monkeypatch) :
    """ test_create_put_slottypes_no_prefix"""
    lex, context, builder, slot_builder = setup
    cfn_create_event['ResourceProperties'].pop('NamePrefix')
    cfn_create_event['ResourceProperties']['name'] = 'LexBot'

    builder.put.return_value = {"name": 'LexBot', "version": '$LATEST' }

    slot_builder.put_slot_type.return_value = {"pizzasize": 'LexBot', "version": '$LATEST' }

    def builder_bot_stub(event, context):
        return builder

    def builder_slot_stub(context):
        return slot_builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)
    monkeypatch.setattr(app, "slot_builder_instance", builder_slot_stub)

    response = app.create(cfn_create_event, context)

    slot_builder.put_slot_type.assert_called_once_with('pizzatype', ['thin', 'thick'])
    assert response['BotName'] == 'LexBot'

def test_create_puts(cfn_create_event, setup, monkeypatch):
    """ test_create_puts_bot"""
    lex, context, builder, _ = setup

    cfn_create_event['ResourceProperties'].pop('slotTypes')
    builder.put.return_value = {"name": BOT_NAME, "version": '$LATEST' }

    def builder_bot_stub(event, context):
        return builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)

    response = app.create(cfn_create_event, context)

    builder.put.assert_called_once_with(BOT_NAME,
            cfn_create_event['ResourceProperties'])

    assert response['BotName'] == BOT_NAME
    assert response['BotVersion'] == BOT_VERSION

def test_update_puts_no_prefix(cfn_create_event, setup, monkeypatch) :
    """ test_update_puts_bot"""
    lex, context, builder, _ = setup
    cfn_create_event['ResourceProperties'].pop('NamePrefix')
    cfn_create_event['ResourceProperties']['name'] = 'LexBot'
    cfn_create_event['ResourceProperties'].pop('slotTypes')

    builder.put.return_value = {"name": 'LexBot', "version": '$LATEST' }

    def builder_bot_stub(event, context):
        return builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)

    response = app.create(cfn_create_event, context)

    builder.put.assert_called_once_with('LexBot',
            cfn_create_event['ResourceProperties'])

    assert response['BotName'] == 'LexBot'
    assert response['BotVersion'] == BOT_VERSION


def test_update_puts(cfn_create_event, setup, monkeypatch):
    """ test_update_puts_bot"""
    lex, context, builder, _ = setup

    cfn_create_event['ResourceProperties'].pop('slotTypes')
    builder.put.return_value = {"name": BOT_NAME, "version": '$LATEST' }

    def builder_bot_stub(event, context):
        return builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)

    response = app.create(cfn_create_event, context)

    builder.put.assert_called_once_with(BOT_NAME,
            cfn_create_event['ResourceProperties'])

    assert response['BotName'] == BOT_NAME
    assert response['BotVersion'] == BOT_VERSION

def test_delete(cfn_delete_event, setup, monkeypatch):
    """ test_delete """
    lex, context, builder, _ = setup

    builder.delete.return_value = None
    def builder_bot_stub(event, context):
        return builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)

    app.delete(cfn_delete_event, context)

    builder.delete.assert_called_once_with(BOT_NAME,
            cfn_delete_event['ResourceProperties'])

def test_delete_no_prefix(cfn_delete_event, setup, monkeypatch) :
    """ test_delete_no_prefix """
    lex, context, builder, _ = setup
    cfn_delete_event['ResourceProperties'].pop('NamePrefix')
    cfn_delete_event['ResourceProperties']['name'] = 'LexBot'

    builder.delete.return_value = None
    def builder_bot_stub(event, context):
        return builder

    monkeypatch.setattr(app, "lex_builder_instance", builder_bot_stub)

    app.delete(cfn_delete_event, context)

    builder.delete.assert_called_once_with("LexBot",
            cfn_delete_event['ResourceProperties'])


