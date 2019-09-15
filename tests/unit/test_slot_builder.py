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
        'createdDate': datetime(2019, 1, 1),
        'description': 'slot type description',
        "enumerationValues": [
        {
         "synonyms": [ "string" ],
         "value": "string"
        }
        ],
        "lastUpdatedDate": datetime(2019, 1, 1),
        "valueSelectionStrategy": "ORIGINAL_VALUE",
        "version": '$LATEST'
    }

def stub_intent_get(stubber, intent_name):
   stubber.add_response(
     'get_intent', {'checksum': 'chksum'}, {'name':intent_name, 'version':
                                         ANY})
def stub_not_found_get_request(stubber):
    """stub not found get request"""
    stubber.add_client_error('get_intent', service_error_code='NotFoundException')

def stub_slot_type_creation(stubber, put_slot_type_response, put_slot_type_request):
    stubber.add_response(
        'put_slot_type', put_slot_type_response, put_slot_type_request)

def stub_intent_deletion(stubber, delete_slot_response, delete_request):

    stubber.add_response(
        'delete_slot', delete_slot_response, delete_request)

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
    monkeypatch_account(monkeypatch)

    with Stubber(lex) as stubber:
        slot_builder = SlotBuilder(Mock(), context, lex_sdk=lex)
        stub_values = [{
                    'value': 'thin',
                    'synonyms':    ['skinny']
                }]
        stub_slot_type_creation(stubber, put_slot_type_response,
                put_slot_type_request(SLOT_TYPE_NAME, synonyms=stub_values))
        synonyms = {'thin': ['skinny']}

        slot_builder.put_slot_type(SLOT_TYPE_NAME, synonyms=synonyms)

        stubber.assert_no_pending_responses()

def test_update_slot_type(put_intent_response, mocker,
        lex, aws_lambda, monkeypatch):
    context = mock_context(mocker)

    monkeypatch_account(monkeypatch)
    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:

        slot_builder = SlotBuilder(Mock(), context, lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'conclusion': 'concluded'
        }
        put_request = put_intent_request(BOT_NAME,
                                          INTENT_NAME, UTTERANCES, plaintext=plaintext)
        put_request.update(put_request_conclusion(plaintext))
        put_request.update({'checksum': 'chksum'})
        stub_intent_get(stubber, INTENT_NAME)

        stub_intent_creation(stubber, put_intent_response, put_request)

        response = slot_builder.put_intent(BOT_NAME, INTENT_NAME,
                UTTERANCES, plaintext=plaintext)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

        assert response['intentName'] == 'greeting'
        assert response['intentVersion'] == '1'

def test_create_intent_conclusion_and_followUp_errors(put_intent_response, mocker,
        lex, aws_lambda, monkeypatch):
    context = mock_context(mocker)

    monkeypatch_account(monkeypatch)
    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        slot_builder = SlotBuilder(Mock(), context, lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'conclusion': 'the conclusion',
            'followUpPrompt': 'follow up'
        }

        stub_not_found_get_request(stubber)
        put_request = put_intent_request(BOT_NAME,
                INTENT_NAME, UTTERANCES, plaintext=plaintext)
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(stubber, put_intent_response, put_request)

        with pytest.raises(Exception) as excinfo:
            slot_builder.put_intent(BOT_NAME, INTENT_NAME, UTTERANCES, plaintext=plaintext)

        assert "Can not have conclusion and followUpPrompt" in str(excinfo.value)

def test_delete_slot(lex, mocker, aws_lambda):
    delete_intent_response, delete_request_1 = {}, {'name': INTENT_NAME}
    delete_intent_response, delete_request_2 = {}, {'name': INTENT_NAME_2}

    context = mock_context(mocker)
    slot_builder = SlotBuilder(Mock(), context, lex_sdk=lex, lambda_sdk=aws_lambda)

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_intent_get(stubber, INTENT_NAME)
        stub_intent_deletion(stubber, delete_intent_response, delete_request_1)
        stub_intent_get(stubber, INTENT_NAME_2)
        stub_intent_deletion(stubber, delete_intent_response, delete_request_2)

        slot_builder.delete_intents([INTENT_NAME, INTENT_NAME_2])

        stubber.assert_no_pending_responses()

