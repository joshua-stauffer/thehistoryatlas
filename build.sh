#!/usr/bin/env bash

# This shell script builds the local docker images needed by the application,
# and installs a virtual environment for running scripts and tests.
python3 -m venv test_env
source test_env/bin/activate
pip install --upgrade pip
pip install -r test_requirements.txt
docker build -t pylib ./pylib
docker build -t testlib ./testlib
docker-compose build
echo ""
echo ""
echo "Finished building the History Atlas!"
echo ""
echo "To start the project, run:"
echo "    docker-compose up"
echo "in the root directory."
echo ""
echo "After the project is running, fill the database with either real or"
echo "generated data by running:"
echo "    source test_env/bin/activate && python builder/scripts/mockclient.py"
echo ""
echo "The RabbitMQ admin console is available at:"
echo "    http://localhost:15672"
echo "    username: guest"
echo "    password: guest"
echo ""
echo "The GraphQL interface is available at:"
echo "    http://localhost:4000"
echo ""
echo "    🌎        🌍        🌏  "
echo ""
echo ""
