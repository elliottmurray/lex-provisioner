#!/usr/bin/env python

""" Provision AWS Lex resources using python SDK
"""

import time
import boto3
from botocore.exceptions import ClientError
from lex_helper import LexHelper

class IntentBuilder(LexHelper, object):
    def __init__(self, logger, lex_sdk=None):
        self._logger = logger
        if(lex_sdk == None):
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk

    def _get_lex_sdk(self):
        return boto3.Session().client('lex-models')

    # def put_intent(self, intent_definition):
    def put_intent(self, intent_definition):
        """Create intent and configure any required lambda permissions

        Currently only supports intents that use the same lambda for both
        code hooks (i.e. 'dialogCodeHook' and 'fulfillmentActivity')
        """
        self._logger.info('put intent')

        code_hook = None
        if 'dialogCodeHook' in intent_definition:
            code_hook = intent_definition['dialogCodeHook']

        # TODO if the intent does not need to invoke a lambda, create it
        if code_hook:
            # If the intent needs to invoke a lambda function, we must give it permission to do so
            # before creating the intent.
            arn_tokens = code_hook['uri'].split(':')
            aws_region = arn_tokens[3]
            aws_account_id = arn_tokens[4]
            lambda_sdk = self._get_lambda_sdk()
            statement_id = 'lex-' + aws_region + \
                '-' + intent_definition['name']
            try:
                add_permission_response = lambda_sdk.add_permission(
                    FunctionName=code_hook['uri'],
                    StatementId=statement_id,
                    Action='lambda:InvokeFunction',
                    Principal='lex.amazonaws.com',
                    SourceArn=self._get_intent_arn(
                        intent_definition['name'], aws_region, aws_account_id)
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

        new_intent = self._create_lex_resource(
            self._lex_sdk.put_intent, 'put_intent', intent_definition
        )
        self._logger.info('Created new intent: %s', new_intent)
        return new_intent
