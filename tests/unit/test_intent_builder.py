import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock
import botocore.session
from botocore.stub import Stubber, ANY
import datetime

from utils import ValidationError
from intent_builder import IntentBuilder

aws_region = 'us-east-1'
aws_account_id = '1234567789'
CODEHOOKNAME = 'greetingCodehook'
BOT_NAME = 'test bot'

INTENT_NAME = 'greeting'

def put_request_followUp(plaintext):
    return  {
        'followUpPrompt': {
            'prompt': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': plaintext['followUpPrompt']
                    },
                ],
                'maxAttempts': 3,
                'responseCard': 'string'
            },
            'rejectionStatement': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': plaintext['followUpRejection']
                    },
                ],
                'responseCard': 'string'
            }
        }
    }

def put_request_conclusion(plaintext):
    return {
        'conclusionStatement': {
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': plaintext['conclusion']
                },
            ],
            'responseCard': 'string'
        },
    }


def put_intent_request(bot_name, intent_name, plaintext=None):

    return {
        'name': intent_name,
        'description': "Intent {0} for {1}".format(intent_name, bot_name),
        'slots': [],

        'sampleUtterances': [ 'a test utterance'
        ],
        'confirmationPrompt': {
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': plaintext['confirmation']
                },
            ],
            'maxAttempts': 3,
            'responseCard': 'string'
        },
        'rejectionStatement': {
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': plaintext['rejection']
                },
            ],
            'responseCard': 'string'
        },
       'dialogCodeHook': {
                'uri': "arn:aws:lambda:{0}:{1}:function:{2}Codehook".format(aws_region,
                    aws_account_id, intent_name),
            'messageVersion': '1.0'
        },
        'fulfillmentActivity': {
            'type': 'ReturnIntent'
        }
    }

@pytest.fixture()
def lex():
    return botocore.session.get_session().create_client('lex-models')

@pytest.fixture()
def aws_lambda():
    return botocore.session.get_session().create_client('lambda')

@pytest.fixture()
def put_intent_response():

    return {
        'name': "greeting",
        'description': 'a description',
        'slots': [],

        'sampleUtterances': [
            'some utterance',
        ],
        'confirmationPrompt': {
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'are you sure?'
                },
            ],
            'maxAttempts': 123,
            'responseCard': 'string'
        },
        'rejectionStatement': {
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'Cannot do this now'
                },
            ],
            'responseCard': 'string'
        },
        'followUpPrompt': {
            'prompt': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': 'Anything else you want to do'
                    },
                ],
                'maxAttempts': 123,
                'responseCard': 'string'
            },
            'rejectionStatement': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': 'string'
                    },
                ],
                'responseCard': 'string'
            }
        },
        'conclusionStatement': {
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'string'
                },
            ],
            'responseCard': 'string'
        },
        'dialogCodeHook': {
            'uri': 'arn:aws:lambda:' + aws_region + ':' + aws_account_id +
            ':function:' + CODEHOOKNAME,
            'messageVersion': '1.0'
        },
        'fulfillmentActivity': {
            'type': 'ReturnIntent',
            'codeHook': {
                'uri': 'arn:aws:lambda:' + aws_region + ':' + aws_account_id + ':function:greetingCodehook',
                'messageVersion': 'string'
            }
        },
        'parentIntentSignature': 'string',
        'version': '1',
        'checksum': 'string'
    }

def stub_lambda_request(lambda_stubber, codehook_uri):
    lambda_request = {
        'FunctionName': codehook_uri,
        'StatementId': 'lex-{0}-{1}'.format(aws_region, INTENT_NAME),
        'Action': 'lambda:InvokeFunction',
        'Principal': 'lex.amazonaws.com',
        'SourceArn': ANY
    }
    lambda_stubber.add_response('add_permission', {}, lambda_request)

def stub_intent_creation(stubber, put_intent_response, put_request):
    stubber.add_response(
        'put_intent', put_intent_response, put_request)
    stubber.add_response('create_intent_version', {'name': INTENT_NAME,
                                                   'version': '1'},
                         {'checksum': 'string', 'name': 'greeting'})

def stub_intent_deletion(stubber, delete_intent_response, delete_request):

    stubber.add_response(
        'delete_intent', delete_intent_response, delete_request)

def test_create_intent_missing_rejection_plaintext(put_intent_response, mocker, lex, aws_lambda):
    codehook_uri = 'arn:aws:lambda:{0}:{1}:function:{2}Codehook'.format(aws_region, aws_account_id, INTENT_NAME)

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), lex_sdk=lex, lambda_sdk=aws_lambda)
        plaintext = {
            "confirmation": 'some confirmation message'
        }

        with pytest.raises(Exception):
            intent_builder.put_intent(BOT_NAME, INTENT_NAME, codehook_uri,
                    max_attempts=3, plaintext=plaintext)

def test_create_intent_plaintext(put_intent_response, mocker,
        lex, aws_lambda):
    codehook_uri = 'arn:aws:lambda:{0}:{1}:function:{2}Codehook'.format(aws_region, aws_account_id, INTENT_NAME)

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), lex_sdk=lex, lambda_sdk=aws_lambda)
        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'followUpPrompt':'follow on',
            'followUpRejection':'failed follow on',
            'conclusion': 'concluded'
        }
        put_request = put_intent_request(BOT_NAME,
                                          INTENT_NAME, plaintext=plaintext)
        put_request.update(put_request_followUp(plaintext))
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(stubber, put_intent_response, put_request)

        intent_builder.put_intent(BOT_NAME, INTENT_NAME, codehook_uri,
                max_attempts=3, plaintext=plaintext)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

def test_create_intent_response(put_intent_response, mocker,
        lex, aws_lambda):
    """ test the response from create intent """
    codehook_uri = 'arn:aws:lambda:{0}:{1}:function:{2}Codehook'.format(aws_region, aws_account_id, INTENT_NAME)

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), lex_sdk=lex, lambda_sdk=aws_lambda)
        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'followUpPrompt':'follow on',
            'followUpRejection':'failed follow on',
            'conclusion': 'concluded'
        }
        put_request = put_intent_request(BOT_NAME,
                INTENT_NAME, plaintext=plaintext)
        put_request.update(put_request_followUp(plaintext))
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(stubber, put_intent_response, put_request)

        response = intent_builder.put_intent(BOT_NAME, INTENT_NAME, codehook_uri,
                max_attempts=3, plaintext=plaintext)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

        assert response['intentName'] == 'greeting'
        assert response['intentVersion'] == '1'


def test_create_intent_missing_followUp_plaintext(put_intent_response, mocker,
        lex, aws_lambda):
    codehook_uri = 'arn:aws:lambda:{0}:{1}:function:{2}Codehook'.format(aws_region, aws_account_id, INTENT_NAME)

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), lex_sdk=lex, lambda_sdk=aws_lambda)
        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'conclusion': 'the conclusion'
        }

        put_request = put_intent_request(BOT_NAME,
                INTENT_NAME,plaintext=plaintext)
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(stubber, put_intent_response, put_request)

        intent_builder.put_intent(BOT_NAME, INTENT_NAME, codehook_uri,
                max_attempts=3, plaintext=plaintext)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()



def test_delete_intent(lex, aws_lambda):
    delete_intent_response, deletet_request = {}, {}

    intent_builder = IntentBuilder(Mock(), lex_sdk=lex, lambda_sdk=aws_lambda)
    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_intent_deletion(stubber, delete_intent_response, deletet_request)
        intent_builder.delete_intents(BOT_NAME, INTENT_NAME)


