#!/bin/bash
set -e

DUMP_FILE="/Volumes/seagate_hub/wikidata/data/data/temp/latest-truthy.nt.gz"
DATA_ROOT_DIR="/Volumes/seagate_hub/wikidata/data/data"
LOG_FILE="$DATA_ROOT_DIR/import_full.log"
WIKIBASE_URL="http://localhost:8888"
WDQS_URL="http://localhost:9999"

echo "Starting Wikidata clear and load process..." | tee -a $LOG_FILE
date | tee -a $LOG_FILE

# 1. First, stop all running containers
echo "Stopping all running containers..." | tee -a $LOG_FILE
docker compose down

# 2. Clear existing data
echo "Clearing existing data..." | tee -a $LOG_FILE

# Clear database data
rm -rf $DATA_ROOT_DIR/mysql/*
# Clear WDQS data
rm -rf $DATA_ROOT_DIR/query-service/*
# Clear elasticsearch data
rm -rf $DATA_ROOT_DIR/elasticsearch/*
# Keep images directory but remove contents
mkdir -p $DATA_ROOT_DIR/images
rm -rf $DATA_ROOT_DIR/images/*

echo "Data cleared successfully." | tee -a $LOG_FILE

# 3. Start the services
echo "Starting Wikibase and related services..." | tee -a $LOG_FILE
docker compose up -d

# 4. Wait for services to fully initialize
echo "Waiting for services to initialize (120 seconds)..." | tee -a $LOG_FILE
sleep 120

# 5. Check if Wikibase is running
if ! docker compose ps wikibase | grep -q "Up"; then
  echo "Error: Wikibase container is not running." | tee -a $LOG_FILE
  docker compose logs wikibase | tee -a $LOG_FILE
  exit 1
fi

echo "Wikibase is now running!" | tee -a $LOG_FILE

# 6. Create a temporary directory for processing
TEMP_DIR="$DATA_ROOT_DIR/temp/processing"
mkdir -p $TEMP_DIR

# 7. Load data into WDQS (Query Service)
echo "Loading data into WDQS..." | tee -a $LOG_FILE

# Check if WDQS is ready to accept data
echo "Waiting for WDQS to be ready..." | tee -a $LOG_FILE
docker compose exec -T wdqs /wait-for-it.sh wdqs:9999 -t 300 -- echo "WDQS is up" | tee -a $LOG_FILE

# Load data into WDQS
echo "Beginning data load into WDQS. This may take several hours..." | tee -a $LOG_FILE
docker compose exec -T wdqs /wdqs/loadData.sh -n wdqs -d $DUMP_FILE | tee -a $LOG_FILE

# 8. Update the Blazegraph namespace to ensure the SPARQL endpoint works correctly
echo "Updating Blazegraph namespace configuration..." | tee -a $LOG_FILE
docker compose exec -T wdqs curl -X POST http://localhost:9999/bigdata/namespace/wdqs/properties -d 'com.bigdata.rdf.store.AbstractTripleStore.textIndex=true' | tee -a $LOG_FILE

# 9. Rebuild search index in Wikibase
echo "Rebuilding search index in Wikibase..." | tee -a $LOG_FILE
docker compose exec -T wikibase php /var/www/html/maintenance/rebuildall.php | tee -a $LOG_FILE

echo "Wikidata clear and load process completed successfully!" | tee -a $LOG_FILE
echo "Access your Wikibase instance at: http://localhost:8888" | tee -a $LOG_FILE
echo "Query Service UI available at: http://localhost:8834" | tee -a $LOG_FILE
date | tee -a $LOG_FILE 