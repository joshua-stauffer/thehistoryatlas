#!/bin/bash
set -e

DATA_ROOT_DIR="/Volumes/seagate_hub/wikidata/data/data"
LOG_FILE="$DATA_ROOT_DIR/clear.log"

echo "Starting Wikidata clearing process..." | tee -a $LOG_FILE
date | tee -a $LOG_FILE

# 1. First, stop all running containers
echo "Stopping all running containers..." | tee -a $LOG_FILE
docker compose down

# 2. Clear existing data
echo "Clearing existing data..." | tee -a $LOG_FILE

# Clear database data
echo "Clearing MySQL data..." | tee -a $LOG_FILE
rm -rf $DATA_ROOT_DIR/mysql/*

# Clear WDQS data
echo "Clearing Query Service data..." | tee -a $LOG_FILE
rm -rf $DATA_ROOT_DIR/query-service/*

# Clear elasticsearch data
echo "Clearing ElasticSearch data..." | tee -a $LOG_FILE
rm -rf $DATA_ROOT_DIR/elasticsearch/*

# Keep images directory but remove contents
echo "Clearing images..." | tee -a $LOG_FILE
mkdir -p $DATA_ROOT_DIR/images
rm -rf $DATA_ROOT_DIR/images/*

echo "Data cleared successfully." | tee -a $LOG_FILE
date | tee -a $LOG_FILE

echo "To restart the Wikidata instance, run: docker compose up -d" 