
class EventHandlerError(Exception):
    """Base class for all event handler errors"""
    pass

class CommandHandlerError(Exception):
    def __init__(self):
        """Base class for all command handler errors"""
        pass

# Command Exceptions

class UnknownCommandTypeError(CommandHandlerError):
    def __init__(self, msg='Command with an unknown or poorly formed type ' + \
        'value was passed to the CommandHandler'):
        """Raised when a command of an unrecognized type is passed to the Command Handler"""
        msg=msg

class CitationExistsError(CommandHandlerError):

    def __init__(self, GUID):
        """Raised when attempting to add a citation that already exists in the
        database. Returns the GUID of the existing citation."""
        self.GUID = GUID

class CitationMissingFieldsError(CommandHandlerError):
    """Raised when a citation is missing a field."""
    pass

class GUIDError(CommandHandlerError):
    """Raised when a GUID already exists in the database."""
    def __init__(self, msg="The provided GUID was not unique"):
        
        self.msg = msg

class UnknownTagTypeError(CommandHandlerError):
    def __init__(self, msg):
        """Raised when a tag with an unknown type reaches the command handler."""
        self.msg = msg

# Event Exceptions

class MalformedEventError(EventHandlerError):

    def __init__(self, msg = ' Event with a poorly formatted body ' + \
        'was passed to the EventHandler'):
        """Error raised when the event handler is passed a message with a
        body which doesn't comply to expected formatting."""
        self.msg = msg

class UnknownEventTypeError(EventHandlerError):

    def __init__(self, msg='Event with an unknown or poorly formed type ' + \
        'value was passed to the EventHandler'):
        """Error raised when the event handler is passed a message which
        doesn't have a recognized type field."""
        msg=msg
