from unittest.mock import Mock, patch

import pytest

from the_history_atlas.apps.config import Config
from the_history_atlas.apps.nlp import NaturalLanguageProcessingApp
from the_history_atlas.apps.nlp.state.database import Database as NLPDatabase
from the_history_atlas.apps.readmodel import ReadModelApp


@pytest.mark.skip("manual only")
@patch("the_history_atlas.apps.nlp.nlp.Processor")
def test_nlp_app_load_model(processor):
    nlp_app = NaturalLanguageProcessingApp(
        database_client=Mock(autospec=NLPDatabase),
        readmodel_app=Mock(autospec=ReadModelApp),
        config_app=Mock(autospec=Config),
    )
    nlp_app.load_model()
