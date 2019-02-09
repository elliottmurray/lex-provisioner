#!/usr/bin/env python

""" Provision AWS Lex resources using python SDK
"""

import time
import boto3
from botocore.exceptions import ClientError


class LexBotBuilder:
    """Create/Update different elements that make up a Lex bot"""

    def __init__(self, logger, lex_sdk=None):
        self._logger = logger
        if(lex_sdk == None):
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk

    def _get_lex_sdk(self):
        return boto3.Session().client('lex-models')

    def _get_lambda_sdk(self):
        return boto3.Session().client('lambda')

    def _create_lex_resource(self, func, func_name, properties):
        try:
            response = func(**properties)
            self._logger.info(
                'Created lex resource using %s, response: %s', func_name, response)
            return response
        except Exception as ex:
            self._logger.error(
                'Failed to create lex resource using %s', func_name)
            self._logger.error(ex)
            raise

    def _update_lex_resource(self, func, func_name, checksum, properties):
        try:
            response = func(checksum=checksum, **properties)
            self._logger.info(
                'Created lex resource using %s, response: %s', func_name, response)
            return response
        except Exception as ex:
            self._logger.error(
                'Failed to update lex resource using %s', func_name)
            self._logger.error(ex)
            raise

    def _replace_intent_version(self, bot_definition, intents):
        for intent in bot_definition['intents']:
            intent['intentVersion'] = intents[intent['intentName']]
        return bot_definition

    def _put_bot(self, bot_name, bot_properties):
        """Create/Update bot"""
        locale = 'en-US'
        try:
            get_bot_response = self._lex_sdk.get_bot(name=bot_name, versionOrAlias='$LATEST')
            checksum = get_bot_response['checksum']

        except ClientError as ex:
            http_status_code = None
            if 'ResponseMetadata' in ex.response:
                response_metadata = ex.response['ResponseMetadata']
                if 'HTTPStatusCode' in response_metadata:
                    http_status_code = response_metadata['HTTPStatusCode']
            if http_status_code == 404:
                creation_response = self._create_lex_resource(
                    self._lex_sdk.put_bot, 'put_bot', bot_properties)
                version_response = self._lex_sdk.create_bot_version(
                    name=bot_name, checksum=creation_response['checksum'])
                return version_response
            else:
                self._logger.info('Lex get_bot call failed')
                self._logger.info(ex)
                raise

        update_response = self._update_lex_resource(
            self._lex_sdk.put_bot, 'put_bot', checksum, bot_properties)
        version_response = self._lex_sdk.create_bot_version(
            name=bot_name, checksum=update_response['checksum'])
        return version_response

    def _get_intent_arn(self, intent_name, aws_region, aws_account_id):
        return 'arn:aws:lex:' + aws_region + ':' + aws_account_id \
            + ':intent:' + intent_name + ':*'

    def _create_intent(self, intent_definition):
        """Create intent and configure any required lambda permissions

        Currently only supports intents that use the same lambda for both
        code hooks (i.e. 'dialogCodeHook' and 'fulfillmentActivity')
        """
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

    def _replace_slot_type_version(self, intents_definition, slot_types):
        for intent in intents_definition:
            for slot in intent['slots']:
                if not slot['slotType'].startswith('AMAZON.'):
                    slot['slotTypeVersion'] = slot_types[slot['slotType']]
        return intents_definition

    def _put_intents(self, intents_definition):
        """Create/Update intents and return the new version created for each

        Arguments:
        intents_definition -- array of intent objects containing all properties required by the aws-lex-sdk's put_intent function
        slot_type_versions -- dict that maps slot_type name -> version
        """
        intent_versions = {}
        for intent in intents_definition:
            name = intent['name']
            lookup_version = '$LATEST'
            try:
                get_intent_response = self._lex_sdk.get_intent(
                    name=name, version=lookup_version)
                checksum = get_intent_response['checksum']
            except ClientError as ex:
                http_status_code = None
                if 'ResponseMetadata' in ex.response:
                    response_metadata = ex.response['ResponseMetadata']
                    if 'HTTPStatusCode' in response_metadata:
                        http_status_code = response_metadata['HTTPStatusCode']
                if http_status_code == 404:
                    creation_response = self._create_intent(intent)
                    version_response = self._lex_sdk.create_intent_version(
                        name=name, checksum=creation_response['checksum'])
                    intent_versions[name] = version_response['version']
                    continue
                else:
                    self._logger.info('Lex get_slot_type call failed')
                    self._logger.info(ex)
                    raise

            update_response = self._update_lex_resource(
                self._lex_sdk.put_intent, 'put_intent', checksum, intent)
            version_response = self._lex_sdk.create_intent_version(
                name=name, checksum=update_response['checksum'])
            intent_versions[name] = version_response['version']
        return intent_versions

    def _put_slot_types(self, slot_type_definition):
        """Create/Update slot_types"""
        slot_type_versions = {}
        for slot_type in slot_type_definition:
            name = slot_type['name']
            lookup_version = '$LATEST'
            try:
                get_slot_type_response = self._lex_sdk.get_slot_type(
                    name=name, version=lookup_version)
                checksum = get_slot_type_response['checksum']
            except ClientError as ex:
                http_status_code = None
                if 'ResponseMetadata' in ex.response:
                    response_metadata = ex.response['ResponseMetadata']
                    if 'HTTPStatusCode' in response_metadata:
                        http_status_code = response_metadata['HTTPStatusCode']
                if http_status_code == 404:
                    creation_response = self._create_lex_resource(
                        self._lex_sdk.put_slot_type, 'put_slot_type', slot_type)
                    version_response = self._lex_sdk.create_slot_type_version(
                        name=name, checksum=creation_response['checksum'])
                    slot_type_versions[name] = version_response['version']
                    continue
                else:
                    self._logger.info('Lex get_slot_type call failed')
                    self._logger.info(ex)
                    raise

            update_response = self._update_lex_resource(
                self._lex_sdk.put_slot_type, 'put_slot_type', checksum, slot_type)
            version_response = self._lex_sdk.create_slot_type_version(
                name=name, checksum=update_response['checksum'])
            slot_type_versions[name] = version_response['version']
        return slot_type_versions

    def put(self, bot_name):
        """Create/Update lex-bot resources; bot, intents, slot_types"""
        # slot_type_versions = self._put_slot_types(lex_definition['slot_types'])

        # intents_definition = self._replace_slot_type_version(lex_definition['intents'], slot_type_versions)
        # intent_versions = self._put_intents(intents_definition)

        # bot_definition = self._replace_intent_version(lex_definition['bot'], intent_versions)
        bot_properties = {
            "name": "test",
            "abortStatement": {
                "messages": [
                    {
                        "content": "I'm sorry, but I am having trouble understanding. I'm going to pass you over to one of my team mates (they're human!). Please wait to be connected, they will have any information we have discussed.",
                        "contentType": "PlainText"
                    }
                ]
            },
            "processBehavior": "BUILD",
            "childDirected": False,
            "clarificationPrompt": {
                "maxAttempts": 1,
                "messages": [
                    {
                        "content": "Hmm, I am sorry but I am still learning and I'm not familiar with those words. Could you try again using different words?",
                        "contentType": "PlainText"
                    }
                ]
            },
            "description": "friendly AI chatbot overlord",
            "idleSessionTTLInSeconds": 3000
        }

        bot_response = self._put_bot(bot_name, bot_properties)
        return bot_response

    MAX_DELETE_TRIES = 5
    RETRY_SLEEP = 5

    def _delete_bot(self, bot_definition):
        '''Delete bot'''
        bot_name = bot_definition['name']
        self._logger.info('deleting bot: %s', bot_name)
        count = self.MAX_DELETE_TRIES
        while True:
            try:
                self._lex_sdk.get_bot(name=bot_name, versionOrAlias='')

                self._lex_sdk.delete_bot(name=bot_name)
                self._logger.info('deleted bot: %s', bot_name)
                break
            except NotFoundException as ex:
                self._logger.warning('Lex can not call delete_bot on deleted bot %s.',
                                     bot_name)

            except Exception as ex:
                self._logger.warning('Lex delete_bot call failed')
                self._logger.warning(ex)
                count -= 1
                if count:
                    self._logger.warning(
                        'Lex delete_bot retry: %s. Sleeping for %s seconds',
                        self.MAX_DELETE_TRIES - count,
                        self.RETRY_SLEEP
                    )
                    time.sleep(self.RETRY_SLEEP)
                    continue
                else:
                    self._logger.error('Lex delete_bot call max retries')
                    raise

    def _delete_intents(self, intents_definition):
        '''Delete all intent'''
        for intent in intents_definition:
            name = intent['name']
            self._logger.info('deleting intent: %s', name)
            count = self.MAX_DELETE_TRIES
            while True:
                try:
                    self._lex_sdk.delete_intent(name=name)
                    self._logger.info('successfully deleted intent: %s', name)
                    break
                except Exception as ex:
                    self._logger.warning('Lex delete_intent call failed')
                    self._logger.warning(ex)
                    count -= 1
                    if count:
                        self._logger.warning(
                            'Lex delete_intent retry: %s. Sleeping for %s seconds',
                            self.MAX_DELETE_TRIES - count,
                            self.RETRY_SLEEP
                        )
                        time.sleep(self.RETRY_SLEEP)
                        continue
                    else:
                        self._logger.error(
                            'Lex delete_intent call max retries')
                        raise

    def _delete_slot_types(self, slot_types_definition):
        '''Delete all slot_type'''
        for slot_type in slot_types_definition:
            name = slot_type['name']
            self._logger.info('deleting slot type: %s', name)
            count = self.MAX_DELETE_TRIES
            while True:
                try:
                    self._lex_sdk.delete_slot_type(name=name)
                    self._logger.info(
                        'successfully deleted slot type: %s', name)
                    break
                except Exception as ex:
                    self._logger.warning('Lex delete_slot_type call failed')
                    self._logger.warning(ex)
                    count -= 1
                    if count:
                        self._logger.warning(
                            'Lex delete_slot_type retry: %s. Sleeping for %s seconds',
                            self.MAX_DELETE_TRIES - count,
                            self.RETRY_SLEEP
                        )
                        time.sleep(self.RETRY_SLEEP)
                        continue
                    else:
                        self._logger.error(
                            'Lex delete_slot_type call max retries')
                        raise

    def delete(self, lex_definition):
        """Delete bot, intents, and slot-types"""
        delete_failed = False
        # TODO what about deleting published version(s) of the bot?
        try:
            self._delete_bot(lex_definition['bot'])
        except Exception as ex:
            delete_failed = True

        try:
            self._delete_intents(lex_definition['intents'])
        except Exception as ex:
            delete_failed = True

        try:
            self._delete_slot_types(lex_definition['slot_types'])
        except Exception as ex:
            delete_failed = True

        if delete_failed:
            raise Exception(
                'See logs for details on what resources failed to delete')

        self._logger.info('Successfully deleted bot and associated resources')
