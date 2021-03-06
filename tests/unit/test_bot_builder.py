# import requests
import botocore.session
from botocore.stub import Stubber, ANY

import mock
import pytest
# from pytest_mock import mocker
from unittest.mock import Mock

from bot_builder import LexBotBuilder
from models.bot import Bot
from models.intent import Intent


BOT_NAME = 'pythontestLexBot'
BOT_VERSION = '$LATEST'
LAMBDA_ARN = "arn:aws:lambda:us-east-1:123456789123:function:GreetingLambda"

DESCRIPTION = "friendly AI chatbot overlord"
LOCALE = 'en-US'

MESSAGES = {
    'clarification': 'clarification statement',
    'abortStatement': 'abort statement'
}


@pytest.fixture()
def intent_defs():
    """ Generates intents json"""
    return [{
            "Name": 'greeting',
            "CodehookArn": LAMBDA_ARN,
            "Utterances": ['greetings my friend', 'hello'],
            "maxAttempts": 3,
            "Plaintext": {
                "confirmation": 'a confirmation'
            }},
            {
            "Name": 'farewell',
            "CodehookArn": LAMBDA_ARN,
            "Utterances": ['farewell my friend'],
            "maxAttempts": 3,
            "Plaintext": {
                "confirmation": 'a farewell confirmation'
            }}]


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
def bot_properties():
    """ default prop resources """

    #   'messages': {
    #       'clarification': 'clarification statement',
    #       'abortStatement': 'abort statement'
    #   },
    return {
        "description": DESCRIPTION,

        'locale': 'en-US'
    }


@pytest.fixture()
def put_bot_response():
    """ put bot response """

    return {
        "name": "test bot",
        "locale": LOCALE,
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
        "description": DESCRIPTION,
        "failureReason": "a failure",
        "idleSessionTTLInSeconds": 300,
        "status": "READY",
        "version": "$LATEST"
    }


def put_bot_request(bot_name, intents, messages, has_checksum=False):
    """ put bot request """
    json = []
    for intent in intents:
        json.append({'intentName': intent.intent_name, 'intentVersion': '$LATEST'})

    put_request = {
        'abortStatement': ANY,
        'childDirected': False,
        'clarificationPrompt': {
            'maxAttempts': 1,
            'messages': [
                {
                    'content': messages['clarification'],
                    'contentType': 'PlainText'
                }
            ]
        },
        'description': ANY,
        'idleSessionTTLInSeconds': ANY,
        'name': bot_name,
        'intents': [
            {'intentName': 'greeting', 'intentVersion': '$LATEST'},
            {'intentName': 'farewell', 'intentVersion': '$LATEST'}
        ],
        'locale': ANY,
        'processBehavior': 'BUILD'
    }

    put_request['intents'] = json

    if has_checksum:
        put_request.update({'checksum': ANY})
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
    intent1 = Intent(BOT_NAME,
                     'greeting',
                     LAMBDA_ARN,
                     ['farewell my friend'],
                     None,
                     max_attempts=3,
                     plaintext={'confirmation': 'a greeting confirmation'})

    intent2 = Intent(BOT_NAME,
                     'farewell',
                     LAMBDA_ARN,
                     ['farewell my friend'],
                     None,
                     max_attempts=3,
                     plaintext={'confirmation': 'a farewell confirmation'})

    lex = botocore.session.get_session().create_client('lex-models')
    return lex, [intent1, intent2]


def stub_not_found_get_request(stubber):
    """stub not found get request"""
    stubber.add_client_error('get_bot',
                             http_status_code=404,
                             service_error_code='NotFoundException')


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


def stub_put_bot(stubber, put_bot_response, expected_put_params):
    """ stub put bot"""
    create_bot_version_response, create_bot_version_params = put_bot_version_interaction(BOT_NAME,
                                                                                         BOT_VERSION)
    stubber.add_response('put_bot', put_bot_response, expected_put_params)
    stubber.add_response('create_bot_version',
                         create_bot_version_response, create_bot_version_params)


def mock_context(mocker):
    """ mock context """
    context = mocker.Mock()
    context.aws_request_id = 12345
    context.get_remaining_time_in_millis.return_value = 100000.0
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:773592622512:function:elliott-helloworld'
    return context


@mock.patch('bot_builder.IntentBuilder')
def test_create_puts_bot(intent_builder, put_bot_response, bot_properties, mocker):
    """ test_create_puts_bot"""
    lex, intents = setup()
    expected_put_params = put_bot_request(BOT_NAME, intents, MESSAGES)

    with Stubber(lex) as stubber:
        context = mock_context(mocker)
        intent_builder_instance = stub_put_intent(intent_builder)
        stub_not_found_get_request(stubber)
        stub_put_bot(stubber, put_bot_response, expected_put_params)

        bot_builder = LexBotBuilder(Mock(), context, lex_sdk=lex,
                                    intent_builder=intent_builder_instance)

        bot = Bot.create_bot(BOT_NAME,
                             intents,
                             MESSAGES,
                             **bot_properties)

        response = bot_builder.put(bot)

        assert response['name'] == BOT_NAME
        assert response['version'] == BOT_VERSION
        stubber.assert_no_pending_responses()


@mock.patch('bot_builder.IntentBuilder')
def test_update_puts_bot(intent_builder, intent_defs, put_bot_response, bot_properties, mocker):
    """ test_update_puts_bot"""
    lex, intents = setup()
    expected_put_params = put_bot_request(BOT_NAME,
                                          intents,
                                          MESSAGES,
                                          has_checksum=True)

    with Stubber(lex) as stubber:
        context = mock_context(mocker)
        intent_builder_instance = stub_put_intent(intent_builder)
        stub_get_request(stubber)
        stub_put_bot(stubber, put_bot_response, expected_put_params)

        bot_builder = LexBotBuilder(Mock(), context, lex_sdk=lex,
                                    intent_builder=intent_builder_instance)
        bot = Bot.create_bot(BOT_NAME,
                             intents,
                             MESSAGES,
                             **bot_properties)
        response = bot_builder.put(bot)

        assert response['name'] == BOT_NAME
        assert response['version'] == BOT_VERSION
        stubber.assert_no_pending_responses()


@mock.patch('bot_builder.IntentBuilder')
def test_create_put_intent_called(intent_builder,
                                  put_bot_response,
                                  bot_properties,
                                  mocker):
    """ create put intent called test """
    lex, intents = setup()
    expected_put_params = put_bot_request(BOT_NAME, intents, MESSAGES)

    with Stubber(lex) as stubber:
        context = mock_context(mocker)
        intent_builder_instance = stub_put_intent(intent_builder)
        stub_not_found_get_request(stubber)
        stub_put_bot(stubber, put_bot_response, expected_put_params)

        bot_builder = LexBotBuilder(Mock(), context, lex_sdk=lex,
                                    intent_builder=intent_builder_instance)
        bot = Bot.create_bot(BOT_NAME,
                             intents,
                             MESSAGES,
                             **bot_properties)
        bot_builder.put(bot)

        assert intent_builder_instance.put_intent.call_count == 2
        intent_builder_instance.put_intent.assert_called_with(intents[1])


@mock.patch('bot_builder.IntentBuilder')
def test_delete_bot_called(intent_builder, put_bot_response, bot_properties, mocker):
    """ delete bot called test """

    lex, intents = setup()
    delete_intent_response = {'test': 'response'}

    with Stubber(lex) as stubber:
        context = mocker.Mock()
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.delete_intents.return_value = delete_intent_response

        stub_get_request(stubber)
        stubber.add_response('delete_bot', {}, {'name': BOT_NAME})

        bot_builder = LexBotBuilder(Mock(), context, lex_sdk=lex,
                                    intent_builder=intent_builder_instance)

        bot = Bot.create_bot(BOT_NAME,
                             intents,
                             MESSAGES,
                             **bot_properties)
        bot_builder.delete(bot)
        stubber.assert_no_pending_responses()


@mock.patch('bot_builder.IntentBuilder')
def test_delete_bot_on_deleted_bot(intent_builder, put_bot_response, mocker):
    """ delete bot does not fail test """
    lex, intents = setup()
    delete_intent_response = {'test': 'response'}

    with Stubber(lex) as stubber:
        context = mocker.Mock()
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.delete_intents.return_value = delete_intent_response

        stub_not_found_get_request(stubber)
        stubber.add_response('delete_bot', {}, {'name': BOT_NAME})

        bot_builder = LexBotBuilder(Mock(), context, lex_sdk=lex,
                                    intent_builder=intent_builder_instance)
        bot = Bot.create_bot(BOT_NAME, intents, {})

        bot_builder.delete(bot)

        assert intent_builder_instance.delete_intents.call_count == 1


@mock.patch('bot_builder.IntentBuilder')
def test_delete_bot_intents_called(intent_builder, put_bot_response, mocker):
    lex, intents = setup()
    delete_intent_response = {'test': 'response'}
    # delete_response = {'test': 'bot response'}

    with Stubber(lex) as stubber:
        context = mocker.Mock()
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.delete_intents.return_value = delete_intent_response

        stub_get_request(stubber)
        stubber.add_response('delete_bot', {}, {'name': BOT_NAME})

        bot_builder = LexBotBuilder(Mock(), context, lex_sdk=lex,
                                    intent_builder=intent_builder_instance)
        bot = Bot.create_bot(BOT_NAME, intents, {})

        bot_builder.delete(bot)

        assert intent_builder_instance.delete_intents.call_count == 1
        intent_builder_instance.delete_intents.assert_called_with(['greeting', 'farewell'])
        stubber.assert_no_pending_responses()
