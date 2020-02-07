class Slot(object):
    """ the slot class """
    def __init__(self, name, slot_type, prompt, utterances):
        self.name = name
        slot_type == [] if slot_type is None else slot_type
        self.slot_type = slot_type
        self.prompt = prompt
        self.utterances = utterances

    def validate_slot(self):
        if self.utterances is None:
            raise Exception("Utterances missing in slot %s", self.name)

    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(self, other.__class__):
            return self.name == other.name
        return False

    @classmethod
    def create_slots(cls, slot_definitions):
        """ create slots """
        slots = []
        if (slot_definitions is None):
            return slots

        for slot_def in slot_definitions:
            slot = Slot(slot_def.get('Name'),
                        slot_def.get('Type'),
                        slot_def.get('Prompt'),
                        slot_def.get('Utterances'))
            slots.append(slot)

        return slots
