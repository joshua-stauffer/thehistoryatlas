
class BrokerError(Exception):
    pass

class MissingReplyFieldError(BrokerError):
    """Raised when a client requests an event replay but neglects to supply
    a reply_to address."""
    def __init__(self):
        self.msg = "No reply_to field was supplied: unable to process request to replay"