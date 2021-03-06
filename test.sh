#!/usr/bin/env bash

source test_env/bin/activate

# after editing pylib files, be sure to uncomment the following line for
# at least the first test run:
pip install pylib/event-schema pylib/pybroker pylib/tha-config

# test readmodel
cd readmodel && python -m pytest

# test writemodel
cd ../writemodel && python -m pytest

# test history
cd ../history && python -m pytest

# test eventstore
cd ../eventstore && python -m pytest

# test nlp
cd ../nlp && python -m pytest

# test geo
cd ../geo && python -m pytest

# test pylib
cd ../pylib/event-schema && python -m pytest
# cd ../pybroker && python -m pytest
cd ../tha-config && python -m pytest

# test testlib
cd ../../testlib/tackle && python -m pytest

deactivate