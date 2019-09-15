#!/usr/bin/env python

""" Provision AWS Lex resources using python SDK
"""

import traceback
import time
import boto3
from botocore.exceptions import ClientError

from intent_builder import IntentBuilder
from lex_helper import LexHelper

class SlotBuilder(LexHelper, object):
    def __init__(self, logger, context, lex_sdk=None):
        self._logger = logger
        self._context = context
        if(lex_sdk == None):
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk

    def get_slots(self, slot_definitions):
        return {}

    def put_slot_type(self, name, synonyms):
        enumeration = []
        for key in  synonyms.keys():
            enumeration.append({'value': key, 'synonyms': synonyms[key]})

        exists, checksum = self._slot_type_exists(name)

        if(exists):
            return self._lex_sdk.put_slot_type(name=name, description=name,
                    enumerationValues=enumeration, checksum=checksum,
                    valueSelectionStrategy='ORIGINAL_VALUE')

        else:
            return self._lex_sdk.put_slot_type(name=name, description=name,
                    enumerationValues=enumeration,
                    valueSelectionStrategy='ORIGINAL_VALUE')

    def delete_slot_type(self, name):
        try:
            self._lex_sdk.delete_slot_type(name=name)
            return True
        except ClientError as ex:
            if(self._not_found(ex, 'delete_slot_type')):
                return True 
            if(self._in_use(ex)):
                return False

    def _slot_type_exists(self, name):
      try:
          get_response = self._lex_sdk.get_slot_type(name=name, version='$LATEST')
          self._logger.info(get_response)
          checksum = get_response['checksum']

          return True, checksum

      except ClientError as ex:
          if(self._not_found(ex, 'get_slot_type')):
              return False, None

          self._logger.error('Lex get_slot_tpe call failed')
          raise


