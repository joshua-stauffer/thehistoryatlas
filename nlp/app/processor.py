"""Text processing component for the History Atlas, powered by spaCy.

"""
from collections import defaultdict
import os
import spacy

class Processor:

    def __init__(self, load_model):
        # would like to programatically make this path, but for now this works:
        if load_model:
            self.nlp = spacy.load(R'/app/models/model-best')
        else:
            self.nlp = None

    def parse(self, text: str):
        """Accepts text as input and returns a dict of results keyed by ENTITY_TYPE"""
        doc = self.nlp(text)
        results = defaultdict(list)
        for tok in doc:
            if tok.ent_type_:
                results[tok.ent_type_].append({
                    'char_start': tok.idx,
                    'char_stop': tok.idx + len(tok.text),
                    'text': tok.text})
        return results
