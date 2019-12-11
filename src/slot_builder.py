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
        return {}

    def put_slot_type(self, name, synonyms):
        """ put slot type by name and synonyms """

        self._logger.info('Put slot type %s', name)
        enumeration = []
        for key in synonyms:
            value = synonyms[key]
            enumeration.append({'value': key,
                                'synonyms': value})

        exists, checksum = self._slot_type_exists(name)
        response = None
        if exists:
            response = self._lex_sdk.put_slot_type(name=name, description=name,
                                               enumerationValues=enumeration, checksum=checksum,
                                               valueSelectionStrategy='ORIGINAL_VALUE')
        else:
          response = self._lex_sdk.put_slot_type(name=name, description=name,
                                           enumerationValues=enumeration,
                                           valueSelectionStrategy='ORIGINAL_VALUE')

        self._logger.info("Successfully created slot type %s", name)
        return response

    def delete_slot_type(self, name):
        """ delete slot type by name and synonyms """

        self._logger.info('Delete slot type %s', name)
        try:
            self._lex_sdk.delete_slot_type(name=name)

        except ClientError as ex:
            if not self._not_found(ex, 'delete_slot_type'):                
                self._in_use(ex)

    def _in_use(self, ex):
        func_name = 'delete_slot_type'
        if ex.response['Error']['Code'] == 'ResourceInUseException':
            self._logger.info('Lex %s call failed because resource' + \
                    ' in use', func_name)
            return False
        return True

    def _slot_type_exists(self, name, versionOrAlias='$LATEST'):
        return self._get_resource(self._lex_sdk.get_slot_type, 
                                  'get_slot_type', 
                                  {'name':name, 'version':versionOrAlias})        