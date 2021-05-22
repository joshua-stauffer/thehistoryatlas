
class TooManyRetriesError(Exception):

    def __init__(self):
        self.msg = 'Resource was unavailable, and the allowable amount of retries was exhausted.'