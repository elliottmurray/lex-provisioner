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

    def _bot_put_properties(self, bot_name, messages, **kwargs):
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

    def put(self, bot):
        """create bot"""
        intent_versions = self._put_intents(bot.name, bot.intents)
        self._logger.info(intent_versions)

        bot_response = self._put_bot(bot, intent_versions)
        return bot_response

    def delete(self, bot):
      """delete bot"""
        # TODO what about deleting published version(s) of the bot?
      self._delete_bot(bot.name)
      self._delete_intents(bot.name, bot.intents)

      self._logger.info('Successfully deleted bot and associated resources')

    def _put_intents(self, bot_name, intents):
        intent_versions = []
        for intent in intents:
            intent_versions.append(
                self._intent_builder.put_intent(intent)
            )

        return intent_versions

    def _delete_intents(self, bot_name, intents):
        intent_names = [intent.intent_name for intent in intents]
        # todo fix this so it just passes the intent object

        self._logger.info(intent_names)
        self._intent_builder.delete_intents(intent_names)

    def _bot_exists(self, name, versionOrAlias='$LATEST'):
        return self._get_resource(self._lex_sdk.get_bot,
                                  'get_bot',
                                  {'name':name, 'versionOrAlias':versionOrAlias})

    def _create_bot(self, bot_name, bot_properties):
        bot_exists, checksum = self._bot_exists(bot_name)
        if bot_exists:
            creation_response = self._update_lex_resource(
                self._lex_sdk.put_bot, 'put_bot', checksum, bot_properties)
            return creation_response, creation_response['checksum']

        else:
            self._logger.info(bot_properties)
            creation_response = self._create_lex_resource(
                self._lex_sdk.put_bot, 'put_bot', bot_properties)

            return creation_response, creation_response['checksum']

    def _put_bot(self, bot, intent_versions):
        """Create/Update bot"""
        self._logger.info('Put bot intent_versions %s', bot.name)
        self._logger.info(intent_versions)

        bot_properties = self._bot_put_properties(bot.name, bot.messages, **bot.attrs)
        bot_properties.update({"intents": intent_versions})

        self._logger.info("Bot properties for AWS %s", bot_properties)

        _, checksum = self._create_bot(bot.name, bot_properties)

        version_response = self._create_lex_resource(
            self._lex_sdk.create_bot_version, 'create_bot_version',
            {
                'name': bot.name,
                'checksum': checksum
            })

        self._logger.info("Created bot version %s", bot.name)
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

            except ClientError:
                self._logger.warning('Lex can not call delete_bot on deleted bot %s.',
                                     bot_name)