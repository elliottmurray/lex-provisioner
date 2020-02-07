class Bot(object):

    def __init__(self, name, intents, messages, **kwargs):
        self.name = name
        self.intents = intents
        self.messages = messages
        self.attrs = kwargs

    def validate_bot(self):
        if self.messages is None:
            raise Exception("Messages missing in bot")

    def __eq__(self, other):
        """Override the default Equals behavior"""

        if isinstance(self, other.__class__):
            return (self.name == other.name
                    and self.intents == other.intents
                    and self.messages == other.messages
                    and self.attrs == other.attrs)
        return False

    @classmethod
    def create_bot(cls, name, intents, messages, **kwargs):
        return Bot(name,
                   intents,
                   messages,
                   **kwargs)
