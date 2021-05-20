"""Component to retrain spaCy models on the fly.

May 19th, 2021"""
import spacy
from spacy.tokens import DocBin

logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)

class Trainer:

    def __init__(self, config, db):
        self._db = db
        self._OUT_DIR = config.OUT_DIR

    def _build_doc_bin(self):
        nlp = spacy.blank('en')
        doc_bin = DocBin()
        annotated_text = self._db.get_training_corpus()
        for text, entities in annotated_text:
            doc = nlp.make_doc(text)
            ents = list()
            for start, stop, label in entities:
                span = doc.char_span(
                            start, stop,
                            label=label, 
                            alignment_mode="contract")
                if span is None:
                    log.debug("Skipping entity")
                else:
                    ents.append(span)
            doc.ents = ents
