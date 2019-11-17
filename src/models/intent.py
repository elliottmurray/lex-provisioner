from models.slot import Slot

class Intent(object):

    def __init__(self, bot_name, intent_name, codehook_arn, utterances, slots, **kwargs):
        self.bot_name = bot_name
        self.intent_name = intent_name
        self.codehook_arn = codehook_arn
        self.utterances = utterances
        self.slots = [] if slots == None else slots
        self.attrs = kwargs
#        self._validate_intent()

    def validate_intent(self):
        if self.utterances is None:
            raise Exception("Utterances missing in intents")
        [slot.validate_slot() for slot in self.slots]
        
    def __eq__(self, other):
        """Override the default Equals behavior"""

        if isinstance(self, other.__class__):
            return (self.bot_name == other.bot_name
                and self.intent_name == other.intent_name
                and self.codehook_arn == other.codehook_arn
                and self.utterances == other.utterances
                and self.slots == other.slots
                and self.attrs == other.attrs)
        return False

    @classmethod
    def create_intent(cls, bot_name, intent_definition):
        intent_name, codehook_arn, max_attempts = cls._extract_intent_attributes(intent_definition)
        utterances = intent_definition.get('Utterances')        
        slots = Slot.create_slots(intent_definition.get('Slots'))
        
        max_attempts = intent_definition.get('maxAttempts') if intent_definition.get('maxAttempts') else 3
        return Intent(bot_name, intent_name, codehook_arn, utterances, slots, max_attempts=max_attempts, plaintext=intent_definition.get('Plaintext'))

    @classmethod
    def _extract_intent_attributes(cls, intent_definition):
        intent_name = intent_definition.get('Name')
        codehook_arn = intent_definition.get('CodehookArn')
        max_attempts = intent_definition.get('maxAttempts')
        return intent_name, codehook_arn, max_attempts
