""" entry point for lambda"""
import json # pylint: disable=unresolved-import

# pylint: disable=import-error
import aws_helper
from bot_builder import LexBotBuilder

from slot_builder import SlotBuilder
from models.bot import Bot
from models.intent import Intent
from models.slot_type import SlotType

# pylint: enable=import-error

# initialise logger
logger = aws_helper.log_config({"RequestId": "CONTAINER_INIT"}) # pylint: disable=invalid-name

logger.info('Logging configured')
# set global to track init failures
INIT_FAILED = False

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
            intent['fulfillmentActivity']['codeHook']['uri'],
            aws_region, aws_account_id, name_prefix
        )

    return dict(
        bot=bot,
        intents=intents,
        slot_types=slot_types
    )

def lex_builder_instance(context):
    """Creates an instance of LexBotBuilder"""
    return LexBotBuilder(logger, context)

def slot_builder_instance(context):
    """Creates an instance of SlotBuilder"""
    return SlotBuilder(logger, context)

def _name_prefix(event):
    resource_properties = event.get('ResourceProperties')
    name_prefix = resource_properties.get('NamePrefix')
    return  "" if name_prefix is None else name_prefix

def _bot_name(event):
    return _name_prefix(event) + event['LogicalResourceId']

def _extract_intents(bot_name, resources):
    intents = []
    for json_intent in resources.get('intents'):
        intents.append(Intent.create_intent(bot_name, json_intent))
    return intents

def _validate_intents(intents):
    [intent.validate_intent() for intent in intents]

def create(event, context):
    """
    Handle Create events

    To return a failure to CloudFormation simply raise an exception,
    the exception message will be sent to CloudFormation Events.
    """
    slot_builder = slot_builder_instance(context)
    lex_bot_builder = lex_builder_instance(context)
    resources = event.get('ResourceProperties')

    slot_types = SlotType.create_slot_types(resources.get('slotTypes'), prefix=_name_prefix(event))

    for slot_type in slot_types:    
        slot_builder.put_slot_type(slot_type)

    bot_name = _bot_name(event)

    intents = _extract_intents(bot_name, resources)
    _validate_intents(intents)

    bot = Bot.create_bot(bot_name,
                         intents,
                         resources.get('messages'),
                         locale=resources.get('locale'),
                         description=resources.get('description'))

    bot_put_response = lex_bot_builder.put(bot)

    return dict(
        BotName=bot_put_response['name'],
        BotVersion=bot_put_response['version']
    )

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
    bot_name = _bot_name(event)
    resources = event.get('ResourceProperties')
    intents = _extract_intents(bot_name, resources)
    bot = Bot.create_bot(bot_name,
                         intents,
                         resources.get('messages'),
                         locale=resources.get('locale'),
                         description=resources.get('description'))
    slot_builder = slot_builder_instance(context)
    lex_bot_builder = lex_builder_instance(context)
    lex_bot_builder.delete(bot)

    slot_types = event.get('ResourceProperties').get('slotTypes')
    slot_types = [] if slot_types is None else slot_types

    for slot_type in slot_types:
        name = _name_prefix(event) + slot_type
        slot_builder.delete_slot_type(name)

def lambda_handler(event, context):
    """
    Main handler function, passes off it's work to crhelper's cfn_handler
    """
    # update the logger with event info
    global logger # pylint: disable=invalid-name,global-statement

    logger = aws_helper.log_config(event)
    logger.info('event: %s', json.dumps(event, indent=4, sort_keys=True, default=str))
    return aws_helper.cfn_handler(event, context, create, update, delete, logger,
                                  INIT_FAILED)
