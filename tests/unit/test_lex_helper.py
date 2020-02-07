import boto3
import mock
# import pytest
# from pytest_mock import mocker
# import os

# import botocore.session
# from botocore.stub import Stubber, ANY
from lex_helper import LexHelper

account_id = '123456789012'
aws_region = 'us-east-1'


class StubLexHelper(LexHelper, object):
    def __init__(self, mocker):
        self._logger = mocker.Mock


def monkeypatch_account(mocker, monkeypatch):
    arn_mock = mock.Mock()

    arn = "arn:aws:lambda:us-east-1:123456789012:function:elliott-helloworld"
    monkeypatch.setattr(boto3, 'client', lambda x: arn_mock)
    arn_mock.get_caller_identity.return_value = {'Arn': arn}


def test_create_get_aws_details(mocker, monkeypatch):
    values = {'AWS_REGION': aws_region}
    with mock.patch.dict('os.environ', values):
        monkeypatch_account(mocker, monkeypatch)

        helper = StubLexHelper(mocker)
        account, region = helper._get_aws_details()

        assert account == account_id
        assert region == aws_region
