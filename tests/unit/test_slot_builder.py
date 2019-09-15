import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock
import botocore.session
from botocore.stub import Stubber, ANY
from datetime import datetime
#import datetime

from utils import ValidationError
from slot_builder import SlotBuilder
from lex_helper import LexHelper

aws_region = 'us-east-1'
aws_account_id = '1234567789'

SLOT_TYPE_NAME = 'colours'

@pytest.fixture()
def lex():
    return botocore.session.get_session().create_client('lex-models')

@pytest.fixture()
def aws_lambda():
    return botocore.session.get_session().create_client('lambda')

def put_slot_type_request(slot_name, synonyms=None):

    put_request = {
      'name': slot_name,
      'description': slot_name,
      'valueSelectionStrategy': "ORIGINAL_VALUE"
    }

    if(synonyms == None):
        synonyms = [
              {
                  "synonyms": [ "pyslot", "junitslot" ],
                  "value": "pyslot"
              }
          ]

    put_request.update({"enumerationValues": synonyms})

    return put_request


@pytest.fixture()
def put_slot_type_response():
    return {
        "name": "greeting slot",
        'checksum': 'chksum',
        'description': 'slot type description',
        "enumerationValues": [
            {
             "synonyms": [ "string" ],
             "value": "string"
            }
        ],
        "valueSelectionStrategy": "ORIGINAL_VALUE",
        "version": '$LATEST'
    }

def stub_slot_type_get(stubber, slot_type_name):
   stubber.add_response(
     'get_slot_type', {'checksum': 'chksum'},
        {'name':slot_type_name,
         'version': ANY})

def stub_slot_type_not_found_get(stubber):
    """stub not found get request"""
    stubber.add_client_error('get_slot_type', service_error_code='NotFoundException')

def stub_slot_type_creation(stubber, put_slot_type_response, put_slot_type_request):
    stubber.add_response(
        'put_slot_type', put_slot_type_response, put_slot_type_request)

def stub_slot_type_deletion(stubber, delete_slot_response, delete_request):
    stubber.add_response(
        'delete_slot_type', delete_slot_response, delete_request)

def mock_context(mocker):
    context = mocker.Mock()
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:1234567789:function:helloworld'
    return context

def monkeypatch_account(monkeypatch):
    monkeypatch.setattr(LexHelper, '_get_aws_details', lambda x:
            [aws_account_id, aws_region])


def test_create_slot_type(put_slot_type_response,
        mocker, lex, monkeypatch):
    context = mock_context(mocker)

    with Stubber(lex) as stubber:
        slot_builder = SlotBuilder(Mock(), context, lex_sdk=lex)
        stub_values = [{
                    'value': 'thin',
                    'synonyms':    ['skinny']
                }]

        stub_slot_type_not_found_get(stubber)
        stub_slot_type_creation(stubber, put_slot_type_response,
                put_slot_type_request(SLOT_TYPE_NAME, synonyms=stub_values))
        synonyms = {'thin': ['skinny']}

        slot_builder.put_slot_type(SLOT_TYPE_NAME, synonyms=synonyms)

        stubber.assert_no_pending_responses()

def test_update_slot_type(put_slot_type_response, mocker, lex):
    context = mock_context(mocker)

    with Stubber(lex) as stubber:
        slot_builder = SlotBuilder(Mock(), context, lex_sdk=lex)
        stub_values = [{
            'value': 'thin',
            'synonyms':    ['skinny']
        }]

        put_request = put_slot_type_request(SLOT_TYPE_NAME, synonyms=stub_values)
        put_request.update({'checksum': 'chksum'})

        stub_slot_type_get(stubber, SLOT_TYPE_NAME)
        stub_slot_type_creation(stubber, put_slot_type_response, put_request)
        synonyms = {'thin': ['skinny']}

        response = slot_builder.put_slot_type(SLOT_TYPE_NAME, synonyms=synonyms)

        stubber.assert_no_pending_responses()
        assert response['name'] == 'greeting slot'
        assert response['version'] == '$LATEST'

def test_delete_slot_type(lex, mocker):
    delete_request = {'name': SLOT_TYPE_NAME }

    context = mock_context(mocker)
    slot_builder = SlotBuilder(Mock(), context, lex_sdk=lex)

    with Stubber(lex) as stubber:
        stub_slot_type_deletion(stubber, {}, delete_request)

        slot_builder.delete_slot_type(SLOT_TYPE_NAME)

        stubber.assert_no_pending_responses()

@pytest.mark.skip(reason="no way of currently testing this")
def test_delete_not_found_slot_type(lex, mocker):
    print("DD")

@pytest.mark.skip(reason="no way of currently testing this")
def test_delete_in_use_slot_type(lex, mocker):
    print("DD")


