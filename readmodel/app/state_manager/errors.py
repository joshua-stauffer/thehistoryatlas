
class EventHandlerError(Exception):
    pass

class UnknownEventError(EventHandlerError):
    def __init__(self, unknown_type):
        self.msg = f'Unknown event of type {unknown_type} reached the ReadModel and was rejected.'