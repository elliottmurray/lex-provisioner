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


@pytest.fixture()
def put_bot_response():
    """ put bot response """
    return {
        "name": "test bot",
        "locale": 'en-US',
        "checksum": 'rnd value',
        "abortStatement": {
            "messages": [
                {
                    "content": "I'm sorry, but I am having trouble understanding. I'm going to pass you over to one of my team mates (they're human!). Please wait to be connected, they will have any information we have discussed.",
                    "contentType": "PlainText"
                }
            ]
        },
        "childDirected": True,
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
        "createdDate": 10012019,
        "description": "friendly AI chatbot overlord",
        "failureReason": "a failure",
        "idleSessionTTLInSeconds": 300,
        "status": "READY",
        "version": "$LATEST"
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

def setup():
    """ setup function """
    return  botocore.session.get_session().create_client('lex-models')

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

@mock.patch('put.IntentBuilder')
def test_create_puts_bot(intent_builder, cfn_create_event, put_bot_response,
        mocker):
    """ test_create_puts_bot"""
    lex = setup()
    bot_props = cfn_create_event['ResourceProperties']

    expected_put_params = put_bot_request(BOT_NAME, bot_props, put_bot_response)

    create_bot_version_response, create_bot_version_params = put_bot_version_interaction(BOT_NAME, BOT_VERSION)

    with Stubber(lex) as stubber:
        intent_builder_instance = stub_put_intent(intent_builder)

        stub_not_found_get_request(stubber)

        stubber.add_response('put_bot', put_bot_response, expected_put_params)

        stubber.add_response('create_bot_version',
                             create_bot_version_response, create_bot_version_params)
        context = mock_context(mocker)

        response = app.create(cfn_create_event, context, lex_sdk=lex)
        assert response['BotName'] == BOT_NAME
        assert response['BotVersion'] == BOT_VERSION

        stubber.assert_no_pending_responses()

@mock.patch('put.IntentBuilder')
def test_update_puts_bot(intent_builder, cfn_create_event, put_bot_response, mocker):
    """ test_create_puts_bot"""
    lex = setup()
    bot_props = cfn_create_event['ResourceProperties']
    expected_put_params = put_bot_request(BOT_NAME, bot_props,
                                          put_bot_response, has_checksum=True)

    create_bot_version_response, create_bot_version_params = put_bot_version_interaction(BOT_NAME, BOT_VERSION)

    with Stubber(lex) as stubber:
        intent_builder_instance = stub_put_intent(intent_builder)
        stub_get_request(stubber)

        stubber.add_response('put_bot', put_bot_response, expected_put_params)

        stubber.add_response('create_bot_version',
                             create_bot_version_response, create_bot_version_params)

        context = mock_context(mocker)

        response = app.create(cfn_create_event, context, lex_sdk=lex)
        assert response['BotName'] == BOT_NAME
        assert response['BotVersion'] == BOT_VERSION

        stubber.assert_no_pending_responses()

@mock.patch('put.IntentBuilder')
def test_create_put_intent_called(intent_builder,
                                  cfn_create_event,
                                  get_bot_response,
                                  put_bot_response,
                                  mocker):
    """ create put intent called test """

    lex = setup()
    bot_props = cfn_create_event['ResourceProperties']

    create_bot_version_response, create_bot_version_params = put_bot_version_interaction(BOT_NAME, BOT_VERSION)
    expected_put_params = put_bot_request(BOT_NAME, bot_props, put_bot_response)

    with Stubber(lex) as stubber:
        intent_builder_instance = stub_put_intent(intent_builder)

        stub_not_found_get_request(stubber)
        stubber.add_response('put_bot', put_bot_response, expected_put_params)

        stubber.add_response('create_bot_version',
                             create_bot_version_response, create_bot_version_params)

        context = mock_context(mocker)

        app.create(cfn_create_event, context, lex_sdk=lex)

        assert intent_builder_instance.put_intent.call_count == 2
        intent_builder_instance.put_intent.assert_called_with(BOT_NAME,
                'farewell', LAMBDA_ARN, 
                ['farewell my friend'],
                max_attempts=3,
                plaintext={'confirmation': 'a farewell confirmation'})

@mock.patch('put.IntentBuilder')
def test_create_put_intent_called_error_no_utterance(intent_builder,
                                  cfn_create_event,
                                  get_bot_response,
                                  put_bot_response,
                                  mocker):
    """ create put intent called test """

    lex = setup()
    bot_props = cfn_create_event['ResourceProperties']

    create_bot_version_response, create_bot_version_params = put_bot_version_interaction(BOT_NAME, BOT_VERSION)
    expected_put_params = put_bot_request(BOT_NAME, bot_props, put_bot_response)

    with Stubber(lex) as stubber:
        intent_builder_instance = stub_put_intent(intent_builder)

        stub_not_found_get_request(stubber)
        stubber.add_response('put_bot', put_bot_response, expected_put_params)

        stubber.add_response('create_bot_version',
                             create_bot_version_response, create_bot_version_params)

        context = mocker.Mock()
        del cfn_create_event['ResourceProperties']['intents'][0]['Utterances']
        del cfn_create_event['ResourceProperties']['intents'][1]['Utterances']

        with pytest.raises(Exception) as excinfo:
            app.create(cfn_create_event, context, lex_sdk=lex)

        assert "Utterances missing in intents" in str(excinfo.value)

@mock.patch('put.IntentBuilder')
def test_delete_bot_called(intent_builder, cfn_delete_event, put_bot_response, mocker):
    """ delete bot called test """

    lex = setup()
    bot_props = cfn_delete_event['ResourceProperties']
    delete_intent_response = {'test':'response'}

    delete_response = {'test':'bot response'}
    with Stubber(lex) as stubber:
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.delete_intents.return_value = delete_intent_response

        stub_get_request(stubber)
        stubber.add_response('delete_bot', {},  {'name':BOT_NAME})

        context = mocker.Mock()

        response = app.delete(cfn_delete_event, context, lex_sdk=lex)

@mock.patch('put.IntentBuilder')
def test_delete_bot_on_deleted_bot(intent_builder, cfn_delete_event, put_bot_response, mocker):
    """ delete bot does not fail test """
    lex = setup()
    bot_props = cfn_delete_event['ResourceProperties']
    delete_intent_response = {'test':'response'}

    with Stubber(lex) as stubber:
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.delete_intents.return_value = delete_intent_response

        stub_not_found_get_request(stubber)
        context = mocker.Mock()

        response = app.delete(cfn_delete_event, context, lex_sdk=lex)


@mock.patch('put.IntentBuilder')
def test_delete_bot_intents_called(intent_builder, cfn_delete_event, put_bot_response,
        mocker):
    lex = setup()
    bot_props = cfn_delete_event['ResourceProperties']
    delete_intent_response = {'test':'response'}

    delete_response = {'test':'bot response'}
    with Stubber(lex) as stubber:
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.delete_intents.return_value = delete_intent_response

        stub_get_request(stubber)
        stubber.add_response('delete_bot', {},  {'name':BOT_NAME})

        context = mocker.Mock()

        response = app.delete(cfn_delete_event, context, lex_sdk=lex)

        assert intent_builder_instance.delete_intents.call_count == 1
        intent_builder_instance.delete_intents.assert_called_with(['greeting','farewell'])

