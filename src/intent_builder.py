""" Provision AWS Lex resources using python SDK
"""

import time
import boto3
from botocore.exceptions import ClientError
from lex_helper import LexHelper
from utils import ValidationError

class IntentBuilder(LexHelper, object):

    RETRY_SLEEP = 5
    def __init__(self, logger, context, lex_sdk=None, lambda_sdk=None):
        self._logger = logger
        self._context = context
        if(lex_sdk == None):
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk

        if(lambda_sdk == None):
            self._lambda_sdk = self._get_lambda_sdk()
        else:
            self._lambda_sdk = lambda_sdk

    def put_intent(self, bot_name, intent_name, lambda_name, utterances,
                   max_attempts=3, plaintext=None):
        """Create intent and configure any required lambda permissions

        Currently only supports intents that use the same lambda for both
        code hooks (i.e. 'dialogCodeHook' and 'fulfillmentActivity')
        """
        self._logger.info('put intent')

        codehook_uri = self._get_function_arn(lambda_name)

        self._add_permission_to_lex_to_codehook(codehook_uri, intent_name)
        # TODO if the intent does not need to invoke a lambda, create it
        exists, checksum = self._intent_exists(intent_name)
        if(exists):
            new_intent = self._update_lex_resource(
                self._lex_sdk.put_intent, 'put_intent', checksum, self.put_intent_request(bot_name,
                    intent_name, codehook_uri, utterances, max_attempts, plaintext=plaintext)
            )
            version_response = self._lex_sdk.create_intent_version(name=intent_name,
                                                                   checksum=new_intent['checksum'])

        else:
            new_intent = self._create_lex_resource(
                self._lex_sdk.put_intent, 'put_intent', self.put_intent_request(bot_name,
                    intent_name, codehook_uri, utterances, max_attempts, plaintext=plaintext)
            )
            version_response = self._lex_sdk.create_intent_version(name=intent_name,
                                                                   checksum=new_intent['checksum'])

        self._logger.info('Created new intent: %s', version_response)
        return { "intentName": version_response['name'],
                "intentVersion": version_response['version']}

    def delete_intents(self, intents_definition, max_attempts=2):
        '''Delete all intents in our tuple'''

        self._logger.info('delete all intents')
        for intent in intents_definition:
            if(self._intent_exists(intent)):
                self._delete_lex_resource(self._lex_sdk.delete_intent, 'delete_intent',
                        name=intent)

    def _intent_exists(self, name, versionOrAlias='$LATEST'):
      try:
          get_response = self._lex_sdk.get_intent(name=name,
                                                   version=versionOrAlias)
          self._logger.info(get_response)
          checksum = get_response['checksum']

          return True, checksum

      except ClientError as ex:
          if ex.response['Error']['Code'] == 'NotFoundException':
              self._logger.info('Intent %s not found', name)
              return False, None

          self._logger.error('Lex get_intent call failed')
          raise

    def _create_message(self, messageKey, content, max_attempts=None):
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

        if max_attempts is not None:
            message[messageKey]['maxAttempts'] = int(max_attempts)

        return message

    def _get_confirmation_message(self, plaintext, max_attempts):
        conf = self._create_message('confirmationPrompt', plaintext['confirmation'],
                                    max_attempts)
        rej = self._create_message('rejectionStatement', plaintext['rejection'])
        conf.update(rej)
        return conf

    def _get_followup_message(self, plaintext, max_attempts):
        follow_up = {
            'followUpPrompt':{
                'prompt': {
                    'maxAttempts': int(max_attempts),
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
        return follow_up

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
            utterances, max_attempts=3, plaintext=None):
#               'codeHook': {
#                    'uri': codehook_uri,
#                    'messageVersion': '1.0'
#     }
# for when fulfillment activity needs a codehook this will be needed
        #utterances = [ 'a test utterance', 'another one']

        request = {
            'name': intent_name,
            'description': "Intent {0} for {1}".format(intent_name, bot_name),
            'slots': [],

            'sampleUtterances': utterances,
            'dialogCodeHook': {
                'uri': codehook_uri,
                'messageVersion': '1.0'
            },
            'fulfillmentActivity': {
                'type': 'ReturnIntent'
           }
        }
        self._put_request_confirmation(request, plaintext, max_attempts)
        self._put_request_followUp(request, plaintext, max_attempts)
        self._put_request_conclusion(request, plaintext)

        self._logger.info(request)

        return request


    def _add_permission_to_lex_to_codehook(self, codehook_uri, intent_name):
        if codehook_uri:
            # If the intent needs to invoke a lambda function, we must give it permission to do so
            # before creating the intent.
            self._logger.info("Codehook uri: %s", codehook_uri)
            _, aws_region = self._get_aws_details()
         #   arn_tokens = codehook_uri.split(':')
         #   aws_region = arn_tokens[3]
         #   aws_account_id = arn_tokens[4]
            statement_id = 'lex-' + aws_region + \
                '-' + intent_name
            try:
                add_permission_response = self._lambda_sdk.add_permission(
                    FunctionName=codehook_uri,
                    StatementId=statement_id,
                    Action='lambda:InvokeFunction',
                    Principal='lex.amazonaws.com',
                    SourceArn=codehook_uri
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


