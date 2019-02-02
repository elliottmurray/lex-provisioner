import json

import requests

import os
import json
import crhelper
from put import LexBotBuilder

# initialise logger
logger = crhelper.log_config({"RequestId": "CONTAINER_INIT"})
logger.info('Logging configured')
# set global to track init failures
init_failed = False

try:
    # Place initialization code here
    logger.info("Container initialization completed")
except Exception as ex:
    logger.error(ex, exc_info=True)
    init_failed = ex


LEX_DEFINITION_FILENAME = 'lex-definition.json'
def _read_lex_definition_file(file_name=LEX_DEFINITION_FILENAME):
    """Reads lex definition file (json) which is packaged in the same directory"""
    with open(file_name) as lex_json_file:
        lex_definition = json.load(lex_json_file)
    logger.info('successfully read bot definition from file: %s', file_name)
    return lex_definition

def _get_function_arn(function_name, aws_region, aws_account_id, prefix):
    return 'arn:aws:lambda:' + aws_region + ':' + aws_account_id \
        + ':function:' + prefix + function_name

def _add_prefix(lex_definition, name_prefix, aws_region, aws_account_id):
    """Add _name_prefix to all resource names in a lex-definition

    This will help differentiate lex-resources when running multiple stacks
    in the same AWS account & region
    """
    bot = lex_definition['bot']
    bot['name'] = name_prefix + bot['name']

    bot['intents'] = list(map(
        lambda intent: dict(
            intentName=(name_prefix + intent.pop('intentName')),
            **intent
        ),
        lex_definition['bot']['intents']
    ))

    slot_types = list(
        map(
            lambda slot_type: dict(
                name=(name_prefix + slot_type.pop('name')),
                **slot_type
            ),
            lex_definition['slot_types']
        )
    )

    intents = list(
        map(
            lambda intent: dict(
                name=(name_prefix + intent.pop('name')),
                slots=list(
                    map(
                        lambda slot: dict(
                            slotType=(name_prefix + slot.pop('slotType')),
                            **slot
                        ) if not slot['slotType'].startswith('AMAZON.') else slot,
                        intent.pop('slots')
                    )
                ),
                **intent
            ),
            lex_definition['intents']
        )
    )

    for intent in intents:
        if 'dialogCodeHook' in intent:
            intent['dialogCodeHook']['uri'] = _get_function_arn(
                intent['dialogCodeHook']['uri'], aws_region, aws_account_id, name_prefix
            )
        intent['fulfillmentActivity']['codeHook']['uri'] = _get_function_arn(
            intent['fulfillmentActivity']['codeHook']['uri'], aws_region, aws_account_id, name_prefix
        )

    return dict(
        bot=bot,
        intents=intents,
        slot_types=slot_types
    )

def _lex_builder_instance(event, context):
    """Creates an instance of LexBotBuilder"""
    lex_definition = _read_lex_definition_file()
    resource_properties = event.get('ResourceProperties')

    name_prefix = resource_properties.get('NamePrefix')
    logger.info('name prefix is: %s', name_prefix)
    aws_account_id = context.invoked_function_arn.split(':')[4]
    aws_region = os.environ['AWS_REGION']

    lex_definition_with_prefix = _add_prefix(lex_definition, name_prefix, aws_region, aws_account_id)
    logger.info('lex definition with prefix: %s', lex_definition_with_prefix)

    return lex_definition_with_prefix, LexBotBuilder(logger)

def create(event, context):
    """
    Handle Create events

    To return a failure to CloudFormation simply raise an exception,
    the exception message will be sent to CloudFormation Events.
    """
    lex_definition, lex_bot_builder = _lex_builder_instance(event, context)

    bot_put_response = lex_bot_builder.put(lex_definition)
    response_data = dict(
        BotName=lex_definition['bot']['name'],
        BotVersion=bot_put_response['version']
    )

    return response_data


def update(event, context):
    """
    Handle Update events

    To return a failure to CloudFormation simply raise an exception,
    the exception message will be sent to CloudFormation Events.
    """
    lex_definition, lex_bot_builder = _lex_builder_instance(event, context)

    bot_put_response = lex_bot_builder.put(lex_definition)
    response_data = dict(
        BotName=lex_definition['bot']['name'],
        BotVersion=bot_put_response['version']
    )

    return response_data


def delete(event, context):
    """
    Handle Delete events

    To return a failure to CloudFormation simply raise an exception,
    the exception message will be sent to CloudFormation Events.
    """
    try:
      lex_definition, lex_bot_builder = _lex_builder_instance(event, context)
      lex_bot_builder.delete(lex_definition)
      return
    except FileNotFoundError as ex:
      logger.error("Could not find lex definition file so just exiting.")
      return

def lambda_handler(event, context):
    """
    Main handler function, passes off it's work to crhelper's cfn_handler
    """
    # update the logger with event info
    global logger

    logger = crhelper.log_config(event)
    logger.info('event: %s', json.dumps(event, indent=4, sort_keys=True, default=str))
    return crhelper.cfn_handler(event, context, create, update, delete, logger,
                                init_failed)
