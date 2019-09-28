import json

import requests

import os
import json
import crhelper
from bot_builder import LexBotBuilder
from slot_builder import SlotBuilder

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
            lex_definition.get('intents')
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

def lex_builder_instance(event, context):
    """Creates an instance of LexBotBuilder"""
    return LexBotBuilder(logger, context)

def slot_builder_instance(context):
    """Creates an instance of SlotBuilder"""
    return SlotBuilder(logger, context)

def _bot_name(event):
    resource_properties = event.get('ResourceProperties')
    name_prefix = resource_properties.get('NamePrefix')
    name_prefix = "" if (name_prefix == None) else name_prefix
    return name_prefix + event['LogicalResourceId']

def create(event, context):
    """
    Handle Create events

    To return a failure to CloudFormation simply raise an exception,
    the exception message will be sent to CloudFormation Events.
    """
    slot_builder = slot_builder_instance(context)
    lex_bot_builder = lex_builder_instance(event, context)
    resource_properties = event.get('ResourceProperties')
    slot_types = resource_properties.get('slotTypes')
    slot_types = [] if slot_types == None else slot_types

    print(slot_types)

    for slot_type in slot_types:
        name = slot_type.get('Name')
        synonyms = slot_type.get('Values')
        slot_builder.put_slot_type(name, synonyms)

    bot_put_response = lex_bot_builder.put(_bot_name(event),
            event.get('ResourceProperties'))

    response_data = dict(
        BotName=bot_put_response['name'],
        BotVersion=bot_put_response['version']
    )

    return response_data

def update(event, context):
    """
    Handle Update events

    To return a failure to CloudFormation simply raise an exception,
    the exception message will be sent to CloudFormation Events.
    """
    return create(event, context)

def delete(event, context):
    """
    Handle Delete events

    To return a failure to CloudFormation simply raise an exception,
    the exception message will be sent to CloudFormation Events.
    """
    lex_bot_builder = lex_builder_instance(event, context)
    lex_bot_builder.delete(_bot_name(event),
            event.get('ResourceProperties'))


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
