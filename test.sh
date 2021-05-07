#!/user/bin/env bash

source test_env/bin/activate

# after editing pylib files, be sure to uncomment the following line for
# at least the first test run:
# pip install pylib/event-schema pylib/pybroker pylib/tha-config

# test readmodel
cd readmodel && python -m pytest tests

# test writemodel
cd ../writemodel && python -m pytest tests

# test history
# currently import issues
#cd ../history && python -m pytest tests

# test eventstore
#cd ../eventstore && python -m pytest tests

# test pylib
cd ../pylib/event-schema && python -m pytest tests
#cd ../pybroker && python -m pytest tests
cd ../tha-config && python -m pytest tests

deactivate