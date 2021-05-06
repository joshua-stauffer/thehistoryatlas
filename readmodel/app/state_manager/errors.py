
class EventHandlerError(Exception):
    pass

class MissingEventFieldError(EventHandlerError):
    pass

class DuplicateEventError(EventHandlerError):
    pass

class UnknownEventError(EventHandlerError):
    def __init__(self, unknown_type):
        self.msg = f'Unknown event of type {unknown_type} reached the ReadModel and was rejected.'

class QueryHandlerError(Exception):
    pass

class UnknownQueryError(QueryHandlerError):
    def __init__(self, unknown_type):
        self.msg = f'Unknown query of type {unknown_type} reached the ReadModel and was rejected.'

class UnknownManifestTypeError(QueryHandlerError):
    def __init__(self, unknown_type):
        self.msg = f'Unknown manifest type {unknown_type} reached the ReadModel and was rejected.'

class DatabaseError(Exception):
    pass

class EmptyNameError(DatabaseError):
    def __init__(self, msg):
        self.msg = msg