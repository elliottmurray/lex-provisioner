# from models.intent import Intent


class SlotType(object):

    def __init__(self, name, slots, **kwargs):
        self.name = name
        self.slots = slots
        self.attrs = kwargs

    # def validate_slot_type(self):
    #     if self.messages is None:
    #         raise Exception("Messages missing in slot type")

    def __eq__(self, other):
        """Override the default Equals behavior"""

        if isinstance(self, other.__class__):
            return (self.name == other.name
                    and self.slots == other.slots)
        return False

    @classmethod
    def create_slot_types(cls, resources, prefix=''):
        slot_types = []

        if resources is None:
            return slot_types
        for slot_type in resources:
            name = prefix + slot_type

            slot = SlotType(name, resources[slot_type])
            slot_types.append(slot)

        return slot_types
