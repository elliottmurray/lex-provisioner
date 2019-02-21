#!/usr/bin/env python

""" Provision AWS Lex resources using python SDK
"""

import time
import boto3
from botocore.exceptions import ClientError

from intent_builder import IntentBuilder
from lex_helper import LexHelper

class LexBotBuilder(LexHelper, object):
    """Create/Update different elements that make up a Lex bot"""

    def __init__(self, logger, lex_sdk=None):
        self._logger = logger
        if(lex_sdk == None):
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk

    def _replace_intent_version(self, bot_definition, intents):
        for intent in bot_definition['intents']:
            intent['intentVersion'] = intents[intent['intentName']]
        return bot_definition

    def _put_bot(self, bot_name, bot_properties):
        """Create/Update bot"""
        locale = 'en-US'
        # try:
        #     get_bot_response = self._lex_sdk.get_bot(name=bot_name, versionOrAlias='$LATEST')
        #     checksum = get_bot_response['checksum']

        # except ClientError as ex:
        #     http_status_code = None
        #     if 'ResponseMetadata' in ex.response:
        #         response_metadata = ex.response['ResponseMetadata']
        #         if 'HTTPStatusCode' in response_metadata:
        #             http_status_code = response_metadata['HTTPStatusCode']
        #     if http_status_code == 404:
        #         creation_response = self._create_lex_resource(
        #             self._lex_sdk.put_bot, 'put_bot', bot_properties)
        #         version_response = self._lex_sdk.create_bot_version(
        #             name=bot_name, checksum=creation_response['checksum'])
        #         return version_response
        #     else:
        #         self._logger.info('Lex get_bot call failed')
        #         self._logger.info(ex)
        #         raise
        creation_response = self._create_lex_resource(
                    self._lex_sdk.put_bot, 'put_bot', bot_properties)

        # update_response = self._update_lex_resource(
        #     self._lex_sdk.put_bot, 'put_bot', checksum, bot_properties)
        version_response = self._lex_sdk.create_bot_version(
            name=bot_name, checksum=creation_response['checksum'])
        print(version_response)
        return version_response

    def _get_intent_arn(self, intent_name, aws_region, aws_account_id):
        return 'arn:aws:lex:' + aws_region + ':' + aws_account_id \
            + ':intent:' + intent_name + ':*'


    def _replace_slot_type_version(self, intents_definition, slot_types):
        # todo construct custom slot types and versions for intents
        # for intent in intents_definition:
        #     for slot in intent['slots']:
        #         if not slot['slotType'].startswith('AMAZON.'):
        #             slot['slotTypeVersion'] = slot_types[slot['slotType']]
        return intents_definition

    def _put_intents(self, intents_definition):
       intent_builder = IntentBuilder(self._logger, lex_sdk=self._lex_sdk)
       return intent_builder.put_intent(intents_definition)

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

    def _bot_put_properties(self, bot_name, checksum, resource_properties):
        return {
            "name": bot_name,
            "locale": resource_properties['locale'],
            "intents": [
              {
                  'intentName': 'someName',
                  'intentVersion': '$LATEST'
              },
            ],
            "checksum": checksum,
            "abortStatement": {
                "messages": [
                    {
                        "content": resource_properties['abortStatement']['message'],
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
                        "content": resource_properties['clarification']['message'],
                        "contentType": "PlainText"
                    }
                ]
            },
            "description": resource_properties['description'],
            "idleSessionTTLInSeconds": 3000
        }


    def put(self, bot_name, resource_properties):
        """Create/Update lex-bot resources; bot, intents, slot_types"""
        # slot_type_versions = self._put_slot_types(lex_definition['slot_types'])

        intents_definition = self._replace_slot_type_version(resource_properties['intents'], {})
        intent_versions = self._put_intents(intents_definition)

        checksum = ''
        # bot_definition = self._replace_intent_version(lex_definition['bot'], intent_versions)
        bot_properties = self._bot_put_properties(bot_name, checksum, resource_properties)

        bot_response = self._put_bot(bot_name, bot_properties)
        return bot_response

    MAX_DELETE_TRIES = 5
    RETRY_SLEEP = 5

    def _delete_bot(self, bot_definition):
        '''Delete bot'''
        # todo fix this
        version = ''
        bot_name = bot_definition['name']
        self._logger.info('deleting bot: %s', bot_name)
        count = self.MAX_DELETE_TRIES
        while True:
            try:
                self._lex_sdk.get_bot(name=bot_name, versionOrAlias=version)

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
