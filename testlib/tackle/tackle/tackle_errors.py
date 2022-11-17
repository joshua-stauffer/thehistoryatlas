class TestError(Exception):
    """Base class for Tackle Errors"""

    pass


class ReplyToFieldNotProvidedError(TestError):
    def __init__(self):
        self.msg = "The client expected a response but no reply to field was provided."
