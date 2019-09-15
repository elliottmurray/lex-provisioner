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

        return self._lex_sdk.put_slot_type(name=name, description=name,
                enumerationValues=enumeration,
                valueSelectionStrategy='ORIGINAL_VALUE')

