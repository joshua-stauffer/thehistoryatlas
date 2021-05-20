#!/usr/bin/env bash

# This shell script builds the local docker images needed by the application.

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
