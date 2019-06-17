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
  def get_slots(self, slot_definitions):
    return {}

