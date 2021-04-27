
class EventHandlerError(Exception):
    """Base class for all event handler errors"""
    pass

class CommandHandlerError(Exception):
    """Base class for all command handler errors"""
    pass

# Command Exceptions

class UnknownCommandTypeError(CommandHandlerError):
    def __init__(self, msg='Command with an unknown or poorly formed type ' + \
        'value was passed to the CommandHandler'):
        msg=msg

class CitationExistsError(CommandHandlerError):
    """Raised when attempting to add a citation that already exists in the
    database. Returns the GUID of the existing citation."""
    def __init__(self, GUID):
        self.GUID = GUID

class CitationMissingFieldsError(CommandHandlerError):
    """Raised when a citation is missing a field on its payload"""
    pass

# Event Exceptions

class PersistedEventError(EventHandlerError):
    def __init__(self, msg):
        self.msg = msg

class UnknownEventTypeError(EventHandlerError):
    def __init__(self, msg='Event with an unknown or poorly formed type ' + \
        'value was passed to the EventHandler'):
        msg=msg
