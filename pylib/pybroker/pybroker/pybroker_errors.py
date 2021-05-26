class BrokerError(Exception):
    pass

class MissingReplyFieldError(BrokerError):
    """Raised when a client requests an event replay but neglects to supply
    a expected elements such as the reply_to address or correlation_id."""
    def __init__(self):
        self.msg = "Request is missing expected elements, possibly the \
                    reply_to or correlation_id fields. \
                    Unable to process the request."

