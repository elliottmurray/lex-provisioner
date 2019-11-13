#!/usr/bin/env python

""" Provision AWS Lex resources using python SDK
"""

import traceback
import time
import boto3
from botocore.exceptions import ClientError

from intent_builder import IntentBuilder
from slot_builder import SlotBuilder
from lex_helper import LexHelper
from models.intent import Intent

class LexBotBuilder(LexHelper):

    MAX_DELETE_TRIES = 5
    RETRY_SLEEP = 5
    LOCALE = 'en-US'

    """Create/Update different elements that make up a Lex bot"""
    def __init__(self, logger, context, lex_sdk=None, intent_builder=None):
        self._logger = logger
        self._context = context
        if lex_sdk is None:
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk
        if intent_builder is None:

            self._intent_builder = IntentBuilder(self._logger, self._context, lex_sdk=self._lex_sdk)
        else:
            self._intent_builder = intent_builder

    def _replace_intent_version(self, bot_definition, intents):
        for intent in bot_definition['intents']:
            intent['intentVersion'] = intents[intent['intentName']]
        return bot_definition

    def _replace_slot_type_version(self, intents_definition, slot_types):
        # todo construct custom slot types and versions for intents
        # for intent in intents_definition:
        #     for slot in intent['slots']:
        #         if not slot['slotType'].startswith('AMAZON.'):
        #             slot['slotTypeVersion'] = slot_types[slot['slotType']]
        return intents_definition

    def _bot_put_properties(self, bot_name, checksum, messages, **kwargs):

        properties = {
            "name": bot_name,
            "locale": kwargs['locale'],
            "abortStatement": {
                "messages": [
                    {
                        "content": messages['abortStatement'],
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
                        "content": messages['clarification'],
                        "contentType": "PlainText"
                    }
                ]
            },
            "description": kwargs['description'],
            "idleSessionTTLInSeconds": 3000
        }

        return properties

    def put(self, bot_name, intents, messages, **kwargs):
        """Create/Update lex-bot resources; bot, intents, slot_types
        Lex needs locale and description in kwargs
        """
        intent_defs = self._put_intents(bot_name, intents)
        self._logger.info(intent_defs)

        checksum = ''
        bot_properties = self._bot_put_properties(bot_name, checksum, messages, **kwargs)
        bot_properties.update({"intents": intent_defs})

        bot_response = self._put_bot(bot_name, bot_properties)
        return bot_response

    def delete(self, bot_name, resource_properties):
        """Delete bot, intents, and slot-types"""
        delete_failed = False
        # TODO what about deleting published version(s) of the bot?
        try:
            self._delete_bot(bot_name)
        except Exception as ex:
            traceback.print_exc(ex)
            delete_failed = True

        try:
            intents_definition = resource_properties['intents']
            self._delete_intents(bot_name, intents_definition)
        except Exception as ex:
            traceback.print_exc(ex)
            delete_failed = True

        if delete_failed:
            raise Exception(
                'See logs for details on what resources failed to delete')

        self._logger.info('Successfully deleted bot and associated resources')

    def _put_intents(self, bot_name, intents):
        intent_versions = []
        for intent in intents:
            # intent = Intent.create_intent(bot_name, intent_definition)
            intent_versions.append(
                self._intent_builder.put_intent(intent)
            )

        return intent_versions

    def _delete_intents(self, bot_name, intent_definitions):
        intent_names = [intent.get('Name') for intent in intent_definitions]

        self._logger.info(intent_names)
        self._intent_builder.delete_intents(intent_names)


    def _bot_exists(self, name, versionOrAlias='$LATEST'):
        try:
            get_bot_response = self._lex_sdk.get_bot(name=name,
                                                     versionOrAlias=versionOrAlias)
            self._logger.info(get_bot_response)
            checksum = get_bot_response['checksum']

            return True, checksum

        except ClientError as ex:
            http_status_code = None
            if 'ResponseMetadata' in ex.response:
                response_metadata = ex.response['ResponseMetadata']
                if 'HTTPStatusCode' in response_metadata:
                    http_status_code = response_metadata['HTTPStatusCode']
            if http_status_code == 404:
                return False, None

            self._logger.error('Lex get_bot call failed')
            self._logger.error(ex)
            raise ex

    def _put_bot(self, bot_name, bot_properties):
        """Create/Update bot"""

        self._logger.info('Put bot properites %s', bot_name)
        self._logger.info(bot_properties)

        bot_exists, checksum = self._bot_exists(bot_name)
        version_response = None

        if bot_exists:
            creation_response = self._update_lex_resource(
                self._lex_sdk.put_bot, 'put_bot', checksum, bot_properties)
            checksum = creation_response['checksum']

        else:
            self._logger.info(bot_properties)

            creation_response = self._create_lex_resource(
                self._lex_sdk.put_bot, 'put_bot', bot_properties)

            checksum = creation_response['checksum']

        version_response = self._create_lex_resource(
            self._lex_sdk.create_bot_version, 'create_bot_version',
            {
                'name': bot_name,
                'checksum': checksum
            })

        self._logger.info("Created bot version %s", bot_name)
        self._logger.info(version_response)

        return version_response

    def _delete_bot(self, bot_name):
        '''Delete bot'''
        self._logger.info('deleting bot: %s', bot_name)
        while True:
            try:

                bot_exists, _ = self._bot_exists(bot_name)
                if(bot_exists):
                    self._delete_lex_resource(self._lex_sdk.delete_bot, 'delete_bot',
                            name=bot_name)

                    self._logger.info('deleted bot: %s', bot_name)
                    break
                else:
                    break

            except ClientError as ex:
                self._logger.warning('Lex can not call delete_bot on deleted bot %s.',
                                     bot_name)

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


