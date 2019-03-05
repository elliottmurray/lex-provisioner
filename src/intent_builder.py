""" Provision AWS Lex resources using python SDK
"""

import time
import boto3
from botocore.exceptions import ClientError
from lex_helper import LexHelper

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


    # def put_intent(self, intent_definition):
    def put_intent(self, bot_name, intent_name, codehook_uri, maxAttempts=2, plaintext=None):
        """Create intent and configure any required lambda permissions

        Currently only supports intents that use the same lambda for both
        code hooks (i.e. 'dialogCodeHook' and 'fulfillmentActivity')
        """
        self._logger.info('put intent')

        self._add_permission_to_lex_to_codehook(codehook_uri, intent_name)
        # TODO if the intent does not need to invoke a lambda, create it
        new_intent = self._create_lex_resource(
            self._lex_sdk.put_intent, 'put_intent', self.put_intent_request(bot_name,
                intent_name, codehook_uri, maxAttempts, plaintext=plaintext)
        )
        self._logger.info('Created new intent: %s', new_intent)
        return new_intent

    def put_intent_request(self, bot_name, intent_name, codehook_uri,
            maxAttempts, plaintext=None):

        return {
            'name': bot_name,
            'description': "Intent {0} for {1}".format(intent_name, bot_name),
            'slots': [],

            'sampleUtterances': [
            ],
            'confirmationPrompt': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': plaintext['confirmation']
                    },
                ],
                'maxAttempts': maxAttempts,
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
            'followUpPrompt': {
                'prompt': {
                    'messages': [
                        {
                            'contentType': 'PlainText',
                            'content': plaintext['followUpPrompt']
                        },
                    ],
                    'maxAttempts': 123,
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
            },
            'conclusionStatement': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': plaintext['conclusion']
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
                    'messageVersion': 'string'
                }
            },
            'parentIntentSignature': 'string',
            'checksum': 'string'
        }


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


