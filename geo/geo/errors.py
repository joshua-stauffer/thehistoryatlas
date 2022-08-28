
class TooManyRetriesError(Exception):

    def __init__(self):
        self.msg = 'Resource was unavailable, and the allowable amount of retries was exhausted.'

class MessageMissingTypeError(Exception):
    ...

class MessageMissingPayloadError(Exception):
    ...

class UnknownQueryError(Exception):
    ...

class MissingReplyFieldError(Exception):
    ...