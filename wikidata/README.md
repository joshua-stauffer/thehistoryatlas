# Wikibase Local Installation

This repository contains Docker configuration to run a local instance of Wikibase (the software that powers Wikidata).

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone this repository
2. Run the setup script:

```bash
./run-wikidata.sh
```

3. Access Wikibase at: http://localhost:8888
4. Access Query Service (SPARQL) at: http://localhost:8834
5. Access Quickstatements at: http://localhost:8840

## Configuration

The environment configuration is stored in the `.env` file. You can modify this file to change:

- Admin credentials
- Database settings
- Port mappings
- Other Wikibase settings

## Docker Images

This setup uses Docker images from https://github.com/jmformenti/docker-images/tree/master/raspberrypi/wikibase.

## Adding Data

After your Wikibase instance is running, you can add data by:

1. Using the web interface
2. Using the API
3. Using Quickstatements
4. Importing from JSON dumps

## Troubleshooting

If containers fail to start:

```bash
# Check container logs
docker compose logs wikibase
docker compose logs mysql
docker compose logs wdqs

# Restart containers
docker compose down -v
docker compose up -d
```

## Data Persistence

All data is stored in the `./data` directory:

- `./data/mysql`: Database files
- `./data/images`: Uploaded media
- `./data/query-service`: SPARQL query service data
- `./data/elasticsearch`: Search index data
- `./data/dumps`: Data dumps for import/export 