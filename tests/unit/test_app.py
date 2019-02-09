from collections import namedtuple
import json
import requests
import crhelper

import mock
import pytest
from pytest_mock import mocker
from unittest.mock import MagicMock
import botocore.session
from botocore.stub import Stubber
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
            "intents": ["test1", "test2"]
        },
        "ResourceType": "Custom::LexBot",
        "ResponseURL": "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-east-1%3A773592622512%3Astack/elliott-test/db2706d0-2683-11e9-a40a-0a515b01a4a4%7CLexBot%7C23f87176-6197-429a-8fb7-890346bde9dc?AWSAccessKeyId=AKIAJRWMYHFMH4DNUF2Q&Expires=1549075566&Signature=9%2FbjkIyX35f7NRCbdrgIOvbmVes%3D",
        "ServiceToken": "arn:aws:lambda:us-east-1:773592622512:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
        "StackId": "arn:aws:cloudformation:us-east-1:773592622512:stack/python-test/db2706d0-2683-11e9-a40a-0a515b01a4a4"
    }


def test_create(cfn_event, mocker):
    # mocker.patch('crhelper.cfn_handler')
    lex = botocore.session.get_session().create_client('lex-models')

    get_response = {
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

    put_response = {
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

    expected_put_params = {'name': 'pythontestLexBot',
                           "locale": "en-US",
                           "childDirected": True
                           }

    expected_get_params = {
        'name': 'pythontestLexBot', 'versionOrAlias': '$LATEST'}

    with Stubber(lex) as stubber:
        stubber.add_response('get_bot', get_response, expected_get_params)
        stubber.add_response('put_bot', put_response, expected_put_params)

        # service_response = lex.put_bot(name='pythontestLexBot', locale='en-US', childDirected=True)
        # service_response = lex.get_bot(name='pythontestLexBot', versionOrAlias='$LATEST')

        context = mocker.Mock()
        context.aws_request_id = 12345
        context.get_remaining_time_in_millis.return_value = 100000.0

        app.create(cfn_event, context, lex_sdk=lex)

    print("finish")
