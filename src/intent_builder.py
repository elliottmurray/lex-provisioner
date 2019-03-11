""" Provision AWS Lex resources using python SDK
"""

import time
import boto3
from botocore.exceptions import ClientError

#from client.exceptions import NotFoundException
from lex_helper import LexHelper

from utils import ValidationError

CONFIRMATION_PROMPT = {'confirmationPrompt': {
    'success': 'confirmation',
    'fail': 'rejection'
    }
}

FOLLOWUP_PROMPT = {'prompt': {
    'success': 'followUpPrompt',
    'fail': 'followUpRejection'
    }
}

class IntentBuilder(LexHelper, object):
    def __init__(self, logger, lex_sdk=None, lambda_sdk=None):
        self._logger = logger
        if(lex_sdk == None):
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk

        if(lambda_sdk == None):
            self._lambda_sdk = self._get_lambda_sdk()
        else:
            self._lambda_sdk = lambda_sdk

    def _not_found_resource(self, ex):
        http_status_code = None
        if 'ResponseMetadata' in ex.response:
            response_metadata = ex.response['ResponseMetadata']
            if 'HTTPStatusCode' in response_metadata:
                http_status_code = response_metadata['HTTPStatusCode']
        if http_status_code == 404:
            return True
        return False

    def get_latest_checksum(self, intent_name, lookup_version='$LATEST'):
        try:
            get_intent_response = self._lex_sdk.get_intent(name=intent_name, version=lookup_version)
            return get_intent_response['checksum']
        except ClientError as ex:
            self._logger.error(ex)
#            if self._not_found_resource(ex):
#                creation_response = self._create_intent(intent)
#                version_response = self._lex_sdk.create_intent_version(name=intent_name, checksum=creation_response['checksum'])
#                intent_versions[name] = version_response['version']
#            else:
#                self._logger.info('Lex get_slot_type call failed')
            return None

    def put_intent(self, bot_name, intent_name, codehook_uri, maxAttempts=2, plaintext=None):
        """Create intent and configure any required lambda permissions

        Currently only supports intents that use the same lambda for both
        code hooks (i.e. 'dialogCodeHook' and 'fulfillmentActivity')
        """
        self._logger.info('adding permission to codehook')
        self._add_permission_to_lex_to_codehook(codehook_uri, intent_name)
        # TODO if the intent does not need to invoke a lambda, create it
        checksum = self.get_latest_checksum(intent_name)

        print(checksum)

        self._logger.info('put intent')
        new_intent = None
        if checksum != None:
            new_intent = self._create_lex_resource(
                self._lex_sdk.put_intent, 'put_intent', self.put_intent_request(bot_name,
                    intent_name, codehook_uri, maxAttempts, checksum=checksum, plaintext=plaintext)
            )
        else:
            new_intent = self._create_lex_resource(
                self._lex_sdk.put_intent, 'put_intent', self.put_intent_request(bot_name,
                    intent_name, codehook_uri, maxAttempts, plaintext=plaintext)
            )
        self._logger.info('Created new intent: %s', new_intent)
        return new_intent

    def _get_confirmation_message(self, plaintext, maxAttempts):
        conf = self._create_message('confirmationPrompt', plaintext['confirmation'],
                maxAttempts)
        rej = self._create_message('rejectionStatement', plaintext['rejection'])
        conf.update(rej)
        return conf

    def put_intent_request(self, bot_name, intent_name, codehook_uri,
            maxAttempts, checksum=None, plaintext=None):

        response = {
            'name': bot_name,
            'description': "Intent {0} for {1}".format(intent_name, bot_name),
            'slots': [],

            'sampleUtterances': [
            ],
            'conclusionStatement': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': plaintext.get('conclusion', '')
                    },
                ],
                'responseCard': 'string'
            },
            'dialogCodeHook': {
                'uri': codehook_uri,
                'messageVersion': '1.0'
            },
            'fulfillmentActivity': {
                'type': 'ReturnIntent',
                'codeHook': {
                    'uri': codehook_uri,
                    'messageVersion': '1.0'
                }
            },
            'parentIntentSignature': 'string'
        }

        if (checksum != None):
            response.update({'checksum': checksum})

        conf = self._create_message(CONFIRMATION_PROMPT, plaintext, maxAttempts)
        follow_up = self._create_message(FOLLOWUP_PROMPT, plaintext, maxAttempts)
        if (conf is not None):
            response.update(conf)

        if (follow_up is not None):
            response['followUpPrompt'] = follow_up

        print(response)

        self._logger.info(response)
        return response

    def _create_message(self, mapping, plaintext, maxAttempts):
        message_key = list(mapping)[0]
        success_key = mapping[message_key]['success']
        fail_key = mapping[message_key]['fail']

        if (plaintext.get(success_key) is not None) and (plaintext.get(fail_key) is not None):

            success = plaintext[success_key]
            fail  = plaintext[fail_key]
            return  {
                message_key: {
                    'messages': [
                        {
                            'contentType': 'PlainText',
                            'content': success,
                        },
                    ],
                   'maxAttempts': maxAttempts,
                   'responseCard': 'string'
                },
                'rejectionStatement': {
                    'messages': [
                        {
                            'contentType': 'PlainText',
                            'content': fail
                        },
                    ],
                'responseCard': 'string'
                 }
            }

        elif not (plaintext.get(success_key) is None and plaintext.get(fail_key)
                is None):
            raise ValidationError("Must have both rejection and confirmation or " +
                    "neither for {} key. Had {} ".format(message_key, plaintext))
        return None

    def _add_permission_to_lex_to_codehook(self, codehook_uri, intent_name):
        if codehook_uri:
            # If the intent needs to invoke a lambda function, we must give it permission to do so
            # before creating the intent.
            arn_tokens = codehook_uri.split(':')
            aws_region = arn_tokens[3]
            aws_account_id = arn_tokens[4]
            statement_id = 'lex-' + aws_region + \
                '-' + intent_name
            try:
                add_permission_response = self._lambda_sdk.add_permission(
                    FunctionName=codehook_uri,
                    StatementId=statement_id,
                    Action='lambda:InvokeFunction',
                    Principal='lex.amazonaws.com',
                    SourceArn=self._get_intent_arn(
                        intent_name, aws_region, aws_account_id)
                )
                self._logger.info(
                    'Response for adding intent permission to lambda: %s', add_permission_response
                )
            except ClientError as ex:
                if ex.response['Error']['Code'] == 'ResourceConflictException':
                    self._logger.info(
                        'Failed to add permission to lambda, it already exists')
                    self._logger.info(ex)
                else:
                    raise


