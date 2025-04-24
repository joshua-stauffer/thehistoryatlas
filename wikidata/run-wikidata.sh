#!/bin/bash
set -e

# Create required directories
echo "Creating directories..."
mkdir -p data/mysql data/images data/query-service data/elasticsearch data/dumps

# Stop any existing containers
echo "Stopping any existing containers..."
docker compose down -v

# Start the containers
echo "Starting Wikibase and related services..."
docker compose up -d

echo "Waiting for Wikibase to initialize (120 seconds)..."
sleep 120

# Check if Wikibase is running
if ! docker compose ps wikibase | grep -q "Up"; then
  echo "Error: Wikibase container is not running."
  docker compose logs wikibase
  exit 1
fi

echo "Wikibase is now running!"
echo ""
echo "Access your Wikibase instance at: http://localhost:8888"
echo "Query Service UI available at: http://localhost:8834"
echo "Quickstatements available at: http://localhost:8840"
echo ""
echo "Admin credentials:"
echo "Username: admin"
echo "Password: wikiadmin123 (as set in .env file)" 