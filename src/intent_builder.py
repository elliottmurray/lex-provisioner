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

    def put_intent(self, intent):
        """Create intent and configure any required lambda permissions

        Currently only supports intents that use the same lambda for both
        code hooks (i.e. 'dialogCodeHook' and 'fulfillmentActivity')
        """
        self._logger.info('put intent')

        self._add_permission_to_lex_to_codehook(intent)
        # TODO if the intent does not need to invoke a lambda, create it
        exists, checksum = self._intent_exists(intent.intent_name)
        if(exists==False):
            new_intent = self._create_lex_resource(
                self._lex_sdk.put_intent, 'put_intent', self.put_intent_request(intent)
            )
            checksum = new_intent['checksum']

        else:
            new_intent = self._update_lex_resource(
                self._lex_sdk.put_intent, 'put_intent', checksum, self.put_intent_request(intent)
            )
            checksum = new_intent['checksum']

        version_response = self._lex_sdk.create_intent_version(name=intent.intent_name,
                                                               checksum=checksum)

        self._logger.info('Created new intent: %s', version_response)
        return { "intentName": version_response['name'],
                "intentVersion": version_response['version']}

        # bot_name = intent.bot_name
        # intent_name = intent.intent_name
        # codehook_arn = intent.codehook_arn
        # utterances = intent.utterances
        # attrs = intent.attrs
        # return self.put_intent(bot_name, intent_name, codehook_arn, utterances, max_attempts=attrs['max_attempts'], plaintext=attrs['plaintext'])

    # def put_intent(self, bot_name, intent_name, codehook_arn, utterances,
    #                max_attempts=3, plaintext=None):
    #     """Create intent and configure any required lambda permissions

    #     Currently only supports intents that use the same lambda for both
    #     code hooks (i.e. 'dialogCodeHook' and 'fulfillmentActivity')
    #     """
    #     self._logger.info('put intent')

    #     self._add_permission_to_lex_to_codehook(codehook_arn, intent_name)
    #     # TODO if the intent does not need to invoke a lambda, create it
    #     exists, checksum = self._intent_exists(intent_name)
    #     if(exists==False):
    #         new_intent = self._create_lex_resource(
    #             self._lex_sdk.put_intent, 'put_intent', self.put_intent_request(bot_name,
    #                 intent_name, codehook_arn, utterances, max_attempts, plaintext=plaintext)
    #         )
    #         checksum = new_intent['checksum']

    #     else:
    #         new_intent = self._update_lex_resource(
    #             self._lex_sdk.put_intent, 'put_intent', checksum, self.put_intent_request(bot_name,
    #                 intent_name, codehook_arn, utterances, max_attempts, plaintext=plaintext)
    #         )
    #         checksum = new_intent['checksum']

    #     version_response = self._lex_sdk.create_intent_version(name=intent_name,
    #                                                            checksum=checksum)

    #     self._logger.info('Created new intent: %s', version_response)
    #     return { "intentName": version_response['name'],
    #             "intentVersion": version_response['version']}

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

    def _put_request_confirmation(self, request, plaintext, max_attempts):
        if (plaintext.get('rejection') is not None) and (plaintext.get('confirmation')
            is not None):
            request.update(self._get_confirmation_message(plaintext, max_attempts))
        elif not (plaintext.get('rejection') is None and plaintext.get('confirmation')
                is None):
            raise ValidationError("Must have both rejection and confirmation or" +
                    "neither. Had ".format(plaintext))

    def _put_request_followUp(self, request, plaintext, max_attempts):
        if(plaintext.get('followUpPrompt') ==  None):
            return

        if(plaintext.get('conclusion') !=  None):
            raise ValidationError('Can not have conclusion and followUpPrompt ' +
                    'in intent %s', request.get('intent_name'))

        if (plaintext.get('followUpPrompt') is not None) and (plaintext.get('followUpRejection') is not None):
            request.update(self._get_followup_message(plaintext, max_attempts))
        elif not (plaintext.get('followUpPrompt') is None) and  (plaintext.get('followUpPrompt') is None):
            raise ValidationError("Must have both follow up rejection and confirmation or" +
                    "neither. Had ".format(plaintext))


    def _put_request_conclusion(self, request, plaintext):
        if(plaintext.get('conclusion') ==  None):
            return

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

    def put_intent_request(self, intent):
# for when fulfillment activity needs a codehook this will be needed
        #utterances = [ 'a test utterance', 'another one']
# bot_name, intent_name, codehook_uri,
#             utterances, max_attempts=3, plaintext=None
        request = {
            'name': intent.intent_name,
            'description': "Intent {0} for {1}".format(intent.intent_name, intent.bot_name),
            # 'slots': [],
            'sampleUtterances': intent.utterances,
            'dialogCodeHook': {
                'uri': intent.codehook_arn,
                'messageVersion': '1.0'
            },
            'fulfillmentActivity': {
                'type': 'ReturnIntent'
           }
        }

        plaintext= intent.attrs['plaintext']
        max_attempts = intent.attrs.get('max_attempts')
        self._put_request_confirmation(request, plaintext, max_attempts)
        self._put_request_followUp(request, plaintext, max_attempts)
        self._put_request_conclusion(request, plaintext)

        self._logger.info(request)

        return request


    def _add_permission_to_lex_to_codehook(self, intent):
        # codehook_uri, intent_name =
        if intent.codehook_arn:
            # If the intent needs to invoke a lambda function, we must give it permission to do so
            # before creating the intent.
            self._logger.info("Codehook arn: %s", intent.codehook_arn)
            _, aws_region = self._get_aws_details()
            arn_tokens = intent.codehook_arn.split(':')

            # function_name = arn_tokens[5]
            statement_id = 'lex-' + aws_region + '-' + intent.intent_name
            try:
                add_permission_response = self._lambda_sdk.add_permission(
                    FunctionName=intent.codehook_arn,
                    StatementId=statement_id,
                    Action='lambda:invokeFunction',
                    Principal='lex.amazonaws.com',
                    SourceArn=self._get_intent_arn(intent.intent_name)
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


