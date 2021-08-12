#!/usr/bin/env bash

# This shell script builds the local docker images needed by the application,
# and installs a virtual environment for running scripts and tests.
if [ ! -d test_env ] ; then
  echo "Creating Python virtual environment for testing in directory test_env"
  if [ python3 -m venv test_env ] ; then
    echo "Built Python virtual environment test_env"
  else
    echo "Failed to build Python virtual environment, and cannot continue build process."
    exit 1
  fi
else
  echo "Skipping creating a virtual environment: Python venv test_env found."
fi
echo "Installing test dependencies"
if source test_env/bin/activate  ; then
  echo "Using virtual environment"
else
  echo "Failed to activate virtual environment"
  exit 1
fi
pip install --upgrade pip
pip install -r test_requirements.txt
deactivate
echo "Creating project docker image dependencies"
docker build -t pylib ./pylib
docker build -t testlib ./testlib
echo "Building all images"
docker-compose build
if [ ! -d client/node_modules ] ; then
  echo "Installing React client"
  npm --prefix ./client install
else
  echo "React client is already installed"
fi
echo ""
echo ""
echo "Finished building the History Atlas!"
echo ""
echo "To start the project, run:"
echo "    docker-compose up"
echo "in the root directory."
echo ""
echo "💽 After the project is running, fill the database with either real or"
echo "generated data by running:"
echo "    source test_env/bin/activate && python builder/scripts/mockclient.py"
echo ""
echo "🐇 The RabbitMQ admin console is available at:"
echo "    http://localhost:15672"
echo "    username: guest"
echo "    password: guest"
echo ""
echo "🚀 The GraphQL interface is available at:"
echo "    http://localhost:4000"
echo ""
echo "⚛️ To start the React client run:"
echo "    npm --prefix ./client start"
echo ""
echo "  The client will be available at:"
echo "    http://localhost:3000"
echo ""
echo ""
echo "    🌎        🌍        🌏  "
echo ""
echo ""
