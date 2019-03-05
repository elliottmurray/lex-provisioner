import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock
import botocore.session
from botocore.stub import Stubber, ANY
import datetime

from intent_builder import IntentBuilder

aws_region = 'us-east-1'
aws_account_id = '1234567789'
codehookName = 'greetingCodehook'

def put_intent_request(bot_name, intent_name, plaintext=None):
    print(plaintext)

    return {
        'name': bot_name,
        'description': "Intent {0} for {1}".format(intent_name, bot_name),
        'slots': [],

        'sampleUtterances': [
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
        'followUpPrompt': {
            'prompt': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': plaintext['followUpPrompt']
                    },
                ],
                'maxAttempts': 123,
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
        },
        'conclusionStatement': {
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': plaintext['conclusion']
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
            'type': 'ReturnIntent',
            'codeHook': {
                'uri': "arn:aws:lambda:{0}:{1}:function:{2}Codehook".format(aws_region,
                    aws_account_id, intent_name),
                'messageVersion': 'string'
            }
        },
        'parentIntentSignature': 'string',
        'checksum': 'string'
    }

@pytest.fixture()
def put_intent_response():

    return {
        'name': "test bot",
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
            ':function:' + codehookName,
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
        'checksum': 'string'
    }


# @mock.patch('put.IntentBuilder')
def test_create_intent_plaintext(put_intent_response, mocker):
    lex = botocore.session.get_session().create_client('lex-models')
    aws_lambda = botocore.session.get_session().create_client('lambda')
    bot_name = 'test bot'
    intent_name = 'greeting'
    codehook_uri = 'arn:aws:lambda:{0}:{1}:function:{2}Codehook'.format(aws_region, aws_account_id, intent_name)

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        lambda_request = {
                'FunctionName': codehook_uri,
                'StatementId': 'lex-{0}-{1}'.format(aws_region, intent_name),
                'Action': 'lambda:InvokeFunction',
                'Principal': 'lex.amazonaws.com',
                'SourceArn': ANY
        }
        lambda_stubber.add_response('add_permission', {}, lambda_request)

        intent_builder = IntentBuilder(Mock(), lex_sdk=lex, lambda_sdk=aws_lambda)
        plaintext = {
                "confirmation": 'some confirmation message',
                'rejection': 'rejection message',
                'followUpPrompt':'follow on',
                'followUpRejection':'failed follow on',
                'conclusion': 'concluded'
                }


        put_request = put_intent_request(bot_name, intent_name, plaintext)
        stubber.add_response(
            'put_intent', put_intent_response, put_request)

        intent_builder.put_intent(bot_name, intent_name, codehook_uri,
                maxAttempts=3, plaintext=plaintext)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

