""" Provision AWS Lex resources using python SDK
"""

import time
import boto3
from botocore.exceptions import ClientError
from lex_helper import LexHelper
from utils import ValidationError

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

    def _create_message(self, messageKey, content, maxAttempts=None):
        message = {
            messageKey: {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': content,
                    },
                ],
                'responseCard': 'string'
            }
        }

        if maxAttempts is not None:
            message[messageKey]['maxAttempts'] =  maxAttempts

        return message

    def _get_confirmation_message(self, plaintext, maxAttempts):
        conf = self._create_message('confirmationPrompt', plaintext['confirmation'],
                maxAttempts)
        rej = self._create_message('rejectionStatement', plaintext['rejection'])
        conf.update(rej)
        return conf

    def _get_followup_message(self, plaintext, maxAttempts):
        followUp = { 'followUpPrompt':
                {'prompt': {
                        'maxAttempts': maxAttempts,
                        'messages': [
                            {
                                'content': plaintext['followUpPrompt'],
                                'contentType': 'PlainText'
                            }
                        ],
                        'responseCard': 'string'
                    },
                    'rejectionStatement': {
                            'messages': [
                                {
                                    'content': plaintext['followUpRejection'],
                                    'contentType': 'PlainText'
                                }
                            ],
                            'responseCard': 'string'
                        }
                    }
               }
        return followUp

    def _put_request_confirmation(self, request, plaintext, maxAttempts):
        if (plaintext.get('rejection') is not None) and (plaintext.get('confirmation')
            is not None):
            request.update(self._get_confirmation_message(plaintext, maxAttempts))
        elif not (plaintext.get('rejection') is None and plaintext.get('confirmation')
                is None):
            raise ValidationError("Must have both rejection and confirmation or" +
                    "neither. Had ".format(plaintext))

    def _put_request_followUp(self, request, plaintext, maxAttempts):
        if (plaintext.get('followUpPrompt') is not None) and (plaintext.get('followUpRejection') is not None):
            request.update(self._get_followup_message(plaintext, maxAttempts))
        elif not (plaintext.get('followUpPrompt') is None) and  (plaintext.get('followUpPrompt') is None):
            raise ValidationError("Must have both follow up rejection and confirmation or" +
                    "neither. Had ".format(plaintext))


    def _put_request_conclusion(self, request, plaintext):
        request.update({
            'conclusionStatement': {
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': plaintext['conclusion']
                    },
                ],
                'responseCard': 'string'
            },
        })

    def put_intent_request(self, bot_name, intent_name, codehook_uri,
            maxAttempts, plaintext=None):

        request = {
            'name': bot_name,
            'description': "Intent {0} for {1}".format(intent_name, bot_name),
            'slots': [],

            'sampleUtterances': [
            ],
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

        self._put_request_confirmation(request, plaintext, maxAttempts)
        self._put_request_followUp(request, plaintext, maxAttempts)
        self._put_request_conclusion(request, plaintext)

        return request


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


