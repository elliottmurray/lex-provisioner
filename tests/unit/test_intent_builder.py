import mock
import pytest
from pytest_mock import mocker
from unittest.mock import Mock
import botocore.session
from botocore.stub import Stubber, ANY
import datetime

from utils import ValidationError
from intent_builder import IntentBuilder
from lex_helper import LexHelper
from models.intent import Intent
from models.slot import Slot

aws_region = 'us-east-1'
aws_account_id = '1234567789'
CODEHOOKNAME = 'greetingCodehook'
BOT_NAME = 'test bot'

INTENT_NAME = 'greeting'
INTENT_NAME_2 = 'farewell'

UTTERANCES = [ 'a test utterance', 'and another' ]

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

def put_intent_request(bot_name, intent_name, utterances, plaintext=None):

    return {
        'name': intent_name,
        'description': "Intent {0} for {1}".format(intent_name, bot_name),
        'sampleUtterances': utterances,
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

def put_intent_slot_request(intent):
    slot_json = []
    for slot in intent.slots:
        slot_json.append({
            'name': slot.name,
            'sampleUtterances': slot.utterances,
            'slotType': slot.slot_type,
            'slotTypeVersion': '$LATEST',
            'slotConstraint': 'Required',
            'valueElicitationPrompt': {
                'messages': [{                    
                    'content': slot.prompt,
                    'contentType': 'PlainText'
                }],
                'maxAttempts': 3
            }
        })

    request = put_intent_request(intent.bot_name, intent.intent_name, intent.utterances, intent.attrs['plaintext'])

    request.update({'slots': slot_json})
    return request

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
        'checksum': 'chksum'
    }

def stub_lambda_request(lambda_stubber, codehook_uri):
    lambda_request = {
        'FunctionName': codehook_uri,
        'StatementId': 'lex-{0}-{1}'.format(aws_region, INTENT_NAME),
        'Action': 'lambda:invokeFunction',
        'Principal': 'lex.amazonaws.com',
        'SourceArn': ANY
    }
    lambda_stubber.add_response('add_permission', {}, lambda_request)

def stub_intent_get(stubber, intent_name):
   stubber.add_response('get_intent', 
                        {'checksum': 'chksum'}, 
                        {'name':intent_name, 'version':
                        ANY})

def stub_not_found_get_request(stubber):
    """stub not found get request"""
    stubber.add_client_error('get_intent', service_error_code='NotFoundException')

def stub_intent_creation(stubber, response, request):
    stubber.add_response('put_intent', response, request)
    stubber.add_response('create_intent_version', {'name': INTENT_NAME,
                                                   'version': '1'},
                         {'checksum': 'chksum', 'name': 'greeting'})

def stub_intent_deletion(stubber, response, request):
    stubber.add_response('delete_intent', response, request)

@pytest.fixture()
def mock_context(mocker):
    context = mocker.Mock()
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:1234567789:function:helloworld'
    return context

@pytest.fixture()
def codehook_uri():
    return 'arn:aws:lambda:{0}:{1}:function:{2}'.format(aws_region,
            aws_account_id, CODEHOOKNAME)

@pytest.fixture()
def monkeypatch_account(monkeypatch):
    monkeypatch.setattr(LexHelper, '_get_aws_details', lambda x:
            [aws_account_id, aws_region])

def test_create_intent_missing_rejection_plaintext(put_intent_response,
        codehook_uri, mock_context, lex, aws_lambda, monkeypatch_account):

    plaintext = {
        "confirmation": 'some confirmation message'
    }

    intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                   UTTERANCES, [], plaintext=plaintext)

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as lex_stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)
        stub_not_found_get_request(lex_stubber)

        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

        with pytest.raises(Exception) as excinfo:
            intent_builder.put_intent(intent)

        assert "Must have both rejection and confirmation or neither" in str(excinfo.value)

def test_create_intent_old_missing_rejection_plaintext(put_intent_response,
        codehook_uri, mock_context, lex, aws_lambda, monkeypatch_account):

   with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as lex_stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)
        stub_not_found_get_request(lex_stubber)

        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)
        plaintext = {
            "confirmation": 'some confirmation message'
        }
        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                   UTTERANCES, [], plaintext=plaintext)
        with pytest.raises(Exception) as excinfo:
            intent_builder.put_intent(intent)
        
        assert "Must have both rejection and confirmation or neither" in str(excinfo.value)

def test_create_intent_plaintext_conclusion(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as lex_stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'conclusion': 'concluded'
        }
        stub_not_found_get_request(lex_stubber)
        put_request = put_intent_request(BOT_NAME,
                                         INTENT_NAME, 
                                         UTTERANCES, 
                                         plaintext=plaintext)
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(lex_stubber, put_intent_response, put_request)
        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, None, plaintext=plaintext, max_attempts=3)
        intent_builder.put_intent(intent)

        lex_stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

def test_create_intent_with_slot(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as lex_stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'conclusion': 'concluded'
        }
        stub_not_found_get_request(lex_stubber)
        slot = Slot('person', 'AMAZON.Person', 'yo', ['one', 'two'])
        # intent = Intent('a', 'b', 'c', 'd', [slot], plaintext=plaintext)
        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, [slot], plaintext=plaintext, max_attempts=3)

        put_request = put_intent_slot_request(intent)
        # put_request = put_intent_request(BOT_NAME,
        #                                   INTENT_NAME, UTTERANCES, plaintext=plaintext)
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(lex_stubber, put_intent_response, put_request)

        intent_builder.put_intent(intent)

        lex_stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

def test_create_intent_plaintext_followup(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)
        stub_not_found_get_request(stubber)
        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'followUpPrompt':'follow on',
            'followUpRejection':'failed follow on'
        }
        
        put_request = put_intent_request(BOT_NAME,
                                          INTENT_NAME, UTTERANCES, plaintext=plaintext)
        put_request.update(put_request_followUp(plaintext))

        stub_intent_creation(stubber, put_intent_response, put_request)
        
        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, None, plaintext=plaintext, max_attempts=3)
        intent_builder.put_intent(intent)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

def test_update_intent_plaintext_conclusion(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):        

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

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

        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, None, plaintext=plaintext, max_attempts=3)
        response = intent_builder.put_intent(intent)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

        assert response['intentName'] == 'greeting'
        assert response['intentVersion'] == '1'

def test_update_intent_plaintext_followUp(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):
   

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)

        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'followUpPrompt':'follow on',
            'followUpRejection':'failed follow on'
        }
        put_request = put_intent_request(BOT_NAME,
                                          INTENT_NAME, UTTERANCES, plaintext=plaintext)

        put_request.update(put_request_followUp(plaintext))
        put_request.update({'checksum': 'chksum'})
        stub_intent_get(stubber, INTENT_NAME)

        stub_intent_creation(stubber, put_intent_response, put_request)

        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, None, plaintext=plaintext, max_attempts=3)
        response = intent_builder.put_intent(intent)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

        assert response['intentName'] == 'greeting'
        assert response['intentVersion'] == '1'

def test_create_intent_response(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):
    """ test the response from create intent """
    
    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)
        intent_builder = IntentBuilder(Mock(), 
                                       mock_context(mocker), 
                                       lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'conclusion': 'concluded'
        }

        stub_not_found_get_request(stubber)
        put_request = put_intent_request(BOT_NAME,
                INTENT_NAME, UTTERANCES, plaintext=plaintext)
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(stubber, put_intent_response, put_request)

        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, None, plaintext=plaintext, max_attempts=3)
        response = intent_builder.put_intent(intent)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

        assert response['intentName'] == 'greeting'
        assert response['intentVersion'] == '1'

def test_create_intent_missing_followUp_plaintext(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):
   

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)
        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

        plaintext = {
            "confirmation": 'some confirmation message',
            'rejection': 'rejection message',
            'conclusion': 'the conclusion'
        }

        stub_not_found_get_request(stubber)
        put_request = put_intent_request(BOT_NAME,
                INTENT_NAME, UTTERANCES, plaintext=plaintext)
        put_request.update(put_request_conclusion(plaintext))

        stub_intent_creation(stubber, put_intent_response, put_request)

        intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, None, plaintext=plaintext, max_attempts=3)
        intent_builder.put_intent(intent)

        stubber.assert_no_pending_responses()
        lambda_stubber.assert_no_pending_responses()

def test_create_intent_conclusion_and_followUp_errors(put_intent_response, codehook_uri, mock_context,
        lex, aws_lambda, monkeypatch_account):
   

    with Stubber(aws_lambda) as lambda_stubber, Stubber(lex) as stubber:
        stub_lambda_request(lambda_stubber, codehook_uri)
        intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

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
            intent = Intent(BOT_NAME, INTENT_NAME, codehook_uri,
                UTTERANCES, None, plaintext=plaintext, max_attempts=3)
            intent_builder.put_intent(intent)

        assert "Can not have conclusion and followUpPrompt" in str(excinfo.value)

def test_delete_intent(lex, mock_context, aws_lambda):
    delete_intent_response, delete_request_1 = {}, {'name': INTENT_NAME}
    delete_intent_response, delete_request_2 = {}, {'name': INTENT_NAME_2}

   
    intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

    with Stubber(lex) as stubber:
        stub_intent_get(stubber, INTENT_NAME)
        stub_intent_deletion(stubber, delete_intent_response, delete_request_1)
        stub_intent_get(stubber, INTENT_NAME_2)
        stub_intent_deletion(stubber, delete_intent_response, delete_request_2)

        intent_builder.delete_intents([INTENT_NAME, INTENT_NAME_2])

        stubber.assert_no_pending_responses()

def test_delete_deleted_intent(lex, mock_context, aws_lambda):
    delete_intent_response, delete_request_1 = {}, {'name': INTENT_NAME}
    delete_intent_response, delete_request_2 = {}, {'name': INTENT_NAME_2}
   
    intent_builder = IntentBuilder(Mock(), mock_context, lex_sdk=lex, lambda_sdk=aws_lambda)

    with Stubber(lex) as stubber:
        stub_not_found_get_request(stubber)
        stub_intent_deletion(stubber, delete_intent_response, delete_request_1)
        stub_not_found_get_request(stubber)
        stub_intent_deletion(stubber, delete_intent_response, delete_request_2)

        intent_builder.delete_intents([INTENT_NAME, INTENT_NAME_2])

        stubber.assert_no_pending_responses()

