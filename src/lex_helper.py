import boto3

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
                'Created lex resource using %s, response: %s', func_name, response)
            return response
        except Exception as ex:
            self._logger.error(
                'Failed to update lex resource using %s', func_name)
            self._logger.error(ex)
            raise

    def _get_intent_arn(self, intent_name, aws_region, aws_account_id):
        return 'arn:aws:lex:' + aws_region + ':' + aws_account_id \
            + ':intent:' + intent_name + ':*'
