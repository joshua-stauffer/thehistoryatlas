
import string
import hashlib

class TextHasher:
    """Utility class to get a hash representation of a string,
    without considering whitespace and punctuation.
    """

    def __init__(self):
        self.hash_func = hashlib.sha256
        self.stop_chars = set([*string.punctuation, *string.whitespace])

    def get_hash(self, text):
        processed_text = self._preprocess_text(text)
        return self._hash_string(processed_text)

    @staticmethod
    def _hash_string(self, text:str) -> str:
        """Obtains a stable hash of the text and returns it"""
        encoded_text = text.encode()
        return hashlib.sha256(text, usedforsecurity=False).hexdigest()

    def _preprocess_text(self, text:str) -> str:
        return ''.join([c.lower for c in text if c not in self.stop_chars])
