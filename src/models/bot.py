from models.intent import Intent

class Bot(object):

    def __init__(self, name, intents, messages, **kwargs):
        self.name = name
        self.intents = intents
        self.messages = messages
        self.attrs = kwargs

    def validate_bot(self):
        if self.utterances is None:
            raise Exception("Utterances missing in intents")        
        
    def __eq__(self, other):
        """Override the default Equals behavior"""

        if isinstance(self, other.__class__):
            return (self.name == other.name
                and self.intents == other.intents
                and self.messages == other.messages
                and self.attrs == other.attrs)
        return False

    @classmethod
    def create_bot(cls, name, intents, resources, **kwargs):
        messages = resources.get('messages')        
        
        # intent_name, codehook_arn, max_attempts = cls._extract_intent_attributes(intent_definition)
        # utterances = intent_definition.get('Utterances')        
        # # slots = Slot.create_slots(intent_definition.get('Slots'))
        
        # max_attempts = intent_definition.get('maxAttempts') if intent_definition.get('maxAttempts') else 3
        return Bot(name, 
                   intents, 
                   messages, 
                   locale=resources.get('locale'), description=resources.get('description'))

    @classmethod
    def _extract_intent_attributes(cls, intent_definition):
        intent_name = intent_definition.get('Name')
        codehook_arn = intent_definition.get('CodehookArn')
        max_attempts = intent_definition.get('maxAttempts')
        return intent_name, codehook_arn, max_attempts
