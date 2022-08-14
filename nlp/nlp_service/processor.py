"""Text processing component for the History Atlas, powered by spaCy.

"""
from collections import defaultdict
import logging
import spacy


log = logging.getLogger(__name__)
log.setLevel("DEBUG")


class Processor:
    """Wrapper for Named Entity Recognition service powered by spaCy."""

    def __init__(self, load_model: bool):
        # would like to programatically make this path, but for now this works:
        if load_model:
            self.nlp = spacy.load(R"/app/models/model-best")
        else:
            log.warning(
                "No NLP model was loaded because the load_model flag "
                + "passed to Processor was False."
            )
            self.nlp = None

    def parse(self, text: str):
        """Accepts text as input and returns a dict of results keyed by ENTITY_TYPE"""
        log.info(f"Parsing text: {text}")
        doc = self.nlp(text)
        results = defaultdict(list)
        for tok in doc:
            if tok.ent_type_:
                results[tok.ent_type_].append(
                    {
                        "start_char": tok.idx,
                        "stop_char": tok.idx + len(tok.text),
                        "text": tok.text,
                    }
                )
        log.info(f"NLP processing results: {results}")
        return results
