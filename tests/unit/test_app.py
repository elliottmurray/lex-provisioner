import requests
import crhelper

import mock
import pytest
from pytest_mock import mocker
import botocore.session
from botocore.stub import Stubber, ANY
import datetime

import app


@pytest.fixture()
def cfn_event():
    """ Generates Custom CFN create Event"""

    return {
        "LogicalResourceId": "LexBot",
        "RequestId": "1234abcd-1234-123a-1ab9-123456bce9dc",
        "RequestType": "Create",
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

            "intents": ["test1", "test2"]
        },
        "ResourceType": "Custom::LexBot",
        "ResponseURL": "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-east-1%3A773592622512%3Astack/elliott-test/db2706d0-2683-11e9-a40a-0a515b01a4a4%7CLexBot%7C23f87176-6197-429a-8fb7-890346bde9dc?AWSAccessKeyId=AKIAJRWMYHFMH4DNUF2Q&Expires=1549075566&Signature=9%2FbjkIyX35f7NRCbdrgIOvbmVes%3D",
        "ServiceToken": "arn:aws:lambda:us-east-1:773592622512:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
        "StackId": "arn:aws:cloudformation:us-east-1:773592622512:stack/python-test/db2706d0-2683-11e9-a40a-0a515b01a4a4"
    }


@pytest.fixture()
def get_bot_response():
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
                    # "groupNumber": 1
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
    return {
        "name": "test bot",
        "locale": 'en-US',
        "checksum": 'rnd value',
        "abortStatement": {
            "messages": [
                  {
                      "content": "I'm sorry, but I am having trouble understanding. I'm going to pass you over to one of my team mates (they're human!). Please wait to be connected, they will have any information we have discussed.",
                      "contentType": "PlainText"
                      # "groupNumber": 1
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
                    # "groupNumber": 1
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

def put_bot_request(bot_name, bot_props, put_bot_response):
    return {
                            'abortStatement': ANY,
                            'checksum': ANY,
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
                            'intents': [{'intentName': 'someName', 'intentVersion': '$LATEST'}],
                             'locale': put_bot_response['locale'],
                            'processBehavior': 'BUILD'
                          }

def get_bot_request(bot_name, bot_version):
    expected_get_params = {
        'name': bot_name, 'versionOrAlias': bot_version}

def get_put_bot_version_interaction(bot_name, bot_version):
    create_bot_version_response = {
        'name': bot_name,
        'version': bot_version
    }

    create_bot_version_params = {
        'checksum': 'rnd value',
        'name': bot_name
    }
    return create_bot_version_response, create_bot_version_params

def setUp():
    lex = botocore.session.get_session().create_client('lex-models')
    bot_name = 'pythontestLexBot'
    bot_version = '$LATEST'
    return lex, bot_name, bot_version

@mock.patch('put.IntentBuilder')
def test_create_puts_bot(intent_builder, cfn_event, get_bot_response, put_bot_response,
        mocker):
    lex, bot_name, bot_version = setUp()
    bot_props = cfn_event['ResourceProperties']

    expected_put_params = put_bot_request(bot_name, bot_props, put_bot_response)

    create_bot_version_response, create_bot_version_params = get_put_bot_version_interaction(bot_name, bot_version)

    with Stubber(lex) as stubber:
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.put_intent.return_value = True

        # stubber.add_response('get_intent', {'checksum': '1234'})
        # stubber.add_response('put_intent', {})

        stubber.add_response('put_bot', put_bot_response, expected_put_params)

        stubber.add_response('create_bot_version',
            create_bot_version_response, create_bot_version_params)

        context = mocker.Mock()
        context.aws_request_id = 12345
        context.get_remaining_time_in_millis.return_value = 100000.0

        response = app.create(cfn_event, context, lex_sdk=lex)
        assert response['BotName'] == bot_name
        assert response['BotVersion'] == bot_version

        stubber.assert_no_pending_responses()


@mock.patch('put.IntentBuilder')
def test_create_put_intent_called(intent_builder, cfn_event, get_bot_response, put_bot_response, mocker):

    lex, bot_name, bot_version = setUp()

    bot_props = cfn_event['ResourceProperties']

    create_bot_version_response, create_bot_version_params = get_put_bot_version_interaction(bot_name, bot_version)
    expected_put_params = put_bot_request(bot_name, bot_props, put_bot_response)

    with Stubber(lex) as stubber:
        intent_builder_instance = intent_builder.return_value
        intent_builder_instance.put_intent.return_value = True

        stubber.add_response('put_bot', put_bot_response, expected_put_params)

        stubber.add_response('create_bot_version',
            create_bot_version_response, create_bot_version_params)

        context = mocker.Mock()
        response = app.create(cfn_event, context, lex_sdk=lex)
        assert intent_builder_instance.put_intent.call_count == 1
        intent_builder_instance.put_intent.assert_called_with(['test1', 'test2'])


