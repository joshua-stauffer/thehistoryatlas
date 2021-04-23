
import string
import hashlib
import logging

class TextHasher:
    """Utility class to get a hash representation of a string,
    without considering whitespace and punctuation.
    """

    def __init__(self):
        self.hash_func = hashlib.sha256
        self.stop_chars = set([*string.punctuation, *string.whitespace])

    def get_hash(self, text):
        """Processes the text and returns a stable hash"""
        logging.info(f'TextHasher: preparing to hash {text}')
        processed_text = self._preprocess_text(text)
        logging.debug(f'TextHasher: processed text is ({processed_text})')
        return self._hash_string(processed_text)

    @staticmethod
    def _hash_string(text:str) -> str:
        """Obtains a stable hash of the text and returns it"""
        encoded_text = text.encode()
        hash = hashlib.sha256(encoded_text)
        return hash.hexdigest()

    def _preprocess_text(self, text:str) -> str:
        return ''.join([c.lower() for c in text if c not in self.stop_chars])
