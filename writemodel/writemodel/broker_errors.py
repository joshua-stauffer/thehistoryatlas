class BrokerError(Exception):
    """base class for WriteModel.Broker exceptions"""
    pass

class MessageError(BrokerError):
    """Error when processing an AMQP message."""
    def __init__(self, msg):
        self.msg = msg
