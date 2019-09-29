#!/usr/bin/env python
""" Provision AWS Lex resources using python SDK"""

from botocore.exceptions import ClientError

# pylint: disable=import-error
from lex_helper import LexHelper
# pylint: enable=import-error

class SlotBuilder(LexHelper):
    """ slot builder """
    def __init__(self, logger, context, lex_sdk=None):
        self._logger = logger
        self._context = context
        if lex_sdk is None:
            self._lex_sdk = self._get_lex_sdk()
        else:
            self._lex_sdk = lex_sdk

    # pylint: disable=no-self-use
    def get_slots(self, slot_definitions):
        """ get slots """
        print(slot_definitions)
        return {}

    def put_slot_type(self, name, synonyms):
        """ put slot type by name and synonyms """

        self._logger.info('Put slot type %s', name)
#        enumeration = []
#        for synonym in synonyms:
       # enumeration.append(synonym)

        exists, checksum = self._slot_type_exists(name)

        if exists:
            return self._lex_sdk.put_slot_type(name=name, description=name,
                                               enumerationValues=synonyms, checksum=checksum,
                                               valueSelectionStrategy='ORIGINAL_VALUE')
        return self._lex_sdk.put_slot_type(name=name, description=name,
                                           enumerationValues=synonyms,
                                           valueSelectionStrategy='ORIGINAL_VALUE')

    def delete_slot_type(self, name):
        """ delete slot type by name and synonyms """

        self._logger.info('Delete slot type %s', name)
        try:
            self._lex_sdk.delete_slot_type(name=name)
            return True
        except ClientError as ex:
            if self._not_found(ex, 'delete_slot_type'):
                return True
            if self._in_use(ex):
                return False

    def _in_use(self, ex):
        func_name = 'delete_slot_type'
        if ex.response['Error']['Code'] == 'ResourceInUseException':
            self._logger.info('Lex %s call failed because resource' + \
                    ' in use', func_name)
            return True
        return False

    def _slot_type_exists(self, name):
        try:
            get_response = self._lex_sdk.get_slot_type(name=name, version='$LATEST')
            self._logger.info(get_response)
            checksum = get_response['checksum']

            return True, checksum

        except ClientError as ex:
            if self._not_found(ex, 'get_slot_type'):
                return False, None

            self._logger.error('Lex get_slot_tpe call failed')
            raise
