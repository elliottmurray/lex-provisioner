import boto3
import time

from botocore.exceptions import ClientError
import traceback

class LexHelper(object):

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
                'Updated lex resource using %s, response: %s', func_name, response)
            return response
        except Exception as ex:
            self._logger.error(
                'Failed to update lex resource using %s', func_name)
            self._logger.error(ex)
            raise

    MAX_DELETE_TRIES = 5
    RETRY_SLEEP = 5

    def _delete_lex_resource(self, func, func_name, **properties):
        '''Delete lex resource'''
        self._logger.info('%s : %s', func_name, properties)
        count = self.MAX_DELETE_TRIES
        while True:
            try:
                func(**properties)
                self._logger.info('finished %s: %s', func_name, properties)
                break
            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NotFoundException':

                    self._logger.info('Lex %s call failed because resource' + \
                            ' not exist', func_name)
                    break
                self._logger.warning('Lex %s call failed', func_name)
                traceback.print_exc()

    def _get_intent_arn(self, intent_name, aws_region, aws_account_id):
        return 'arn:aws:lex:' + aws_region + ':' + aws_account_id \
            + ':intent:' + intent_name + ':*'
