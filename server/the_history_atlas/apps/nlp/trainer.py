import logging
from subprocess import STDOUT, run
import spacy
from spacy.tokens import DocBin

log = logging.getLogger(__name__)
logging.basicConfig(level="DEBUG")


class Trainer:
    def __init__(self, config, db):
        self._db = db
        self._OUT_DIR = config.TRAIN_DIR

    def build_training_file(self):
        # TODO: divide into training/dev
        nlp = spacy.blank("en")
        doc_bin = DocBin()
        annotated_text = self._db.get_training_corpus()
        for text, entities in annotated_text:
            doc = nlp.make_doc(text)
            ents = list()
            for start, stop, label in entities:
                span = doc.char_span(
                    start, stop, label=label, alignment_mode="contract"
                )
                if span is None:
                    log.debug(
                        f"{label} entity from {start} to {stop} was not "
                        + "valid and was discarded."
                    )
                else:
                    ents.append(span)
            doc.ents = ents
            doc_bin.add(doc)
        # TODO: remove underscore when dev data is available
        data_uri = f"{self._OUT_DIR}/_train.spacy"
        log.info(f"Now saving training file to disk at {data_uri}")
        doc_bin.to_disk(data_uri)

    def train(self):
        """Launch a training script"""
        log.info("Starting training")
        cmd = [
            "python",
            "-m",
            "spacy",
            "train",
            "/app/train/config.cfg",  # config file
            "--output",
            "/app/models",  # output dir
            "--paths.train",
            "/app/train/train.spacy",  # training data
            "--paths.dev",
            "/app/train/dev.spacy",  # validation data
        ]
        res = run(cmd, stderr=STDOUT)
        log.info("training has completed: ", "\n", res)
