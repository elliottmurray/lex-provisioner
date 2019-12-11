from collections import namedtuple
import json
import requests

import mock
import pytest
from pytest_mock import mocker
from unittest.mock import MagicMock

import app

@pytest.fixture()
def cfn_event():
    """ Generates Custom CFN create Event"""

    return  {
        "LogicalResourceId": "LexBot",
        "RequestId": "1234abcd-1234-123a-1ab9-123456bce9dc",
        "RequestType": "Create",
        "ResourceProperties": {
          "NamePrefix": "pythontest",
          "ServiceToken": "arn:aws:lambda:us-east-1:123456789123:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
          "loglevel": "info"
        },
        "ResourceType": "Custom::LexBot",
        "ResponseURL": "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-east-1%3A773592622512%3Astack/elliott-test/db2706d0-2683-11e9-a40a-0a515b01a4a4%7CLexBot%7C23f87176-6197-429a-8fb7-890346bde9dc?AWSAccessKeyId=AKIAJRWMYHFMH4DNUF2Q&Expires=1549075566&Signature=9%2FbjkIyX35f7NRCbdrgIOvbmVes%3D",
        "ServiceToken": "arn:aws:lambda:us-east-1:773592622512:function:lex-provisioner-LexProvisioner-1SADWMED8AJK6",
        "StackId": "arn:aws:cloudformation:us-east-1:773592622512:stack/python-test/db2706d0-2683-11e9-a40a-0a515b01a4a4"
      }

@pytest.mark.skip(reason="no way of currently testing this")
def test_send_cfn_confirmation():
    context = None
    app.send_cfn_confirmation(cfn_event, context)

# def test_lambda_handler(cfn_event, mocker):
#     context = mocker.Mock()
#     context.aws_request_id = 12345
#     context.get_remaining_time_in_millis.return_value=100000.0

#     ret = app.lambda_handler(cfn_event, context)
#     assert ret["statusCode"] == 200

#     for key in ("message", "location"):
#         assert key in ret["body"]

#     data = json.loads(ret["body"])
#     assert data["message"] == "hello world"
