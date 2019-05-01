import mock
import pytest
from pytest_mock import mocker
import os

from lex_helper import LexHelper

class StubLexHelper(LexHelper, object):
    def __init__(self, context, lex_sdk=None):
        self._context = context

def test_create_get_aws_details(mocker):
    context = mocker.Mock()
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:773592622512:function:elliott-helloworld'

    helper = StubLexHelper(context)
    account, region = helper._get_aws_details()

    assert account == '773592622512'
    assert region == 'us-east-1'
