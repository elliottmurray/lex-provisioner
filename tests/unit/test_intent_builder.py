import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock
import botocore.session
from botocore.stub import Stubber, ANY
import datetime

from intent_builder import IntentBuilder

# @mock.patch('put.IntentBuilder')
def test_create_intent(mocker):
    lex = botocore.session.get_session().create_client('lex-models')
    with Stubber(lex) as stubber:
        assert True == True
        intent_builder = IntentBuilder(Mock(), lex_sdk=lex)
        intent_builder.put_intent({})

