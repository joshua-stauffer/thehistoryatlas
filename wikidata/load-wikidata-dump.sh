#!/bin/bash
set -e

DUMP_FILE="/Volumes/seagate_hub/wikidata/data/data/temp/latest-truthy.nt.gz"
DATA_ROOT_DIR="/Volumes/seagate_hub/wikidata/data/data"
LOG_FILE="$DATA_ROOT_DIR/import_full.log"
WIKIBASE_URL="http://localhost:8888"
TEMP_DIR="$DATA_ROOT_DIR/temp/processing"

# Create necessary directories
mkdir -p $TEMP_DIR

echo "Starting Wikidata import process..." | tee -a $LOG_FILE
date | tee -a $LOG_FILE

# Make sure the containers are running
echo "Ensuring all containers are running..." | tee -a $LOG_FILE
docker compose up -d

# Wait for services to be ready
echo "Waiting for services to be fully ready (60 seconds)..." | tee -a $LOG_FILE
sleep 60

# Install necessary tools in the wikibase container
echo "Installing necessary tools in the Wikibase container..." | tee -a $LOG_FILE
docker compose exec -T wikibase apt-get update
docker compose exec -T wikibase apt-get install -y python3 python3-pip

# Create a simple Python script to process the Wikidata dump and load it
echo "Creating import script in the container..." | tee -a $LOG_FILE
cat > $TEMP_DIR/import_wikidata.py << 'EOL'
import gzip
import os
import re
import json
import subprocess
import time
import random
import string
from urllib.parse import quote

# Configuration
dump_file = "/var/lib/mysql/dumps/latest-truthy.nt.gz"
batch_size = 100
log_file = "/var/lib/mysql/dumps/import.log"
max_entities = float('inf')  # Set a limit if needed, or leave as infinity

# Regex pattern to extract QID, property and value from N-Triples
entity_pattern = re.compile(r'<http://www.wikidata.org/entity/(Q\d+)> <([^>]+)> (.+) \.$')
label_pattern = re.compile(r'<http://www.wikidata.org/entity/(Q\d+)> <http://www.w3.org/2000/01/rdf-schema#label> "(.*)"@en \.$')
description_pattern = re.compile(r'<http://www.wikidata.org/entity/(Q\d+)> <http://schema.org/description> "(.*)"@en \.$')

# Store entity data
entities = {}
processed_count = 0
batch_count = 0
qid_map = {}  # Map to store original QID to local ID mapping

def log(message):
    with open(log_file, 'a') as f:
        f.write(f"{message}\n")
    print(message)

def create_entity(qid, label=None, description=None):
    """Create a basic entity structure with the given QID"""
    entity = {
        "id": qid,
        "labels": {},
        "descriptions": {},
        "claims": {}
    }
    
    if label:
        entity["labels"]["en"] = {"language": "en", "value": label}
    
    if description:
        entity["descriptions"]["en"] = {"language": "en", "value": description}
    
    return entity

def run_sql_query(query):
    """Run a direct SQL query on the MariaDB database"""
    cmd = [
        'mysql', 
        '-h', 'localhost', 
        '-u', 'root', 
        '-pwikidataroot', 
        'wikidata', 
        '-e', query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"Error executing SQL: {result.stderr}")
        return result.stdout
    except Exception as e:
        log(f"SQL execution error: {e}")
        return None

def setup_qid_mapping_table():
    """Create a table to store QID mappings"""
    log("Setting up QID mapping table")
    
    # Create the table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS qid_mapping (
        local_id INT NOT NULL,
        original_qid VARCHAR(20) NOT NULL,
        PRIMARY KEY (local_id),
        UNIQUE KEY (original_qid)
    );
    """
    run_sql_query(create_table_query)

def import_entities_batch(batch):
    """Import a batch of entities using the Wikibase API"""
    log(f"Importing batch of {len(batch)} entities")
    
    for qid, entity_data in batch.items():
        # Get label and description
        label = entity_data.get("labels", {}).get("en", {}).get("value", qid)
        description = entity_data.get("descriptions", {}).get("en", {}).get("value", "")
        
        # Escape special characters in the label and description
        label = label.replace('"', '\\"').replace("'", "\\'")
        description = description.replace('"', '\\"').replace("'", "\\'")
        
        # Create the entity using wbeditentity API
        cmd = [
            'curl', '-s', '-X', 'POST',
            'http://localhost/w/api.php',
            '--data-urlencode', 'action=wbeditentity',
            '--data-urlencode', 'format=json',
            '--data-urlencode', 'new=item',
            '--data-urlencode', f'data={{"labels":{{"en":{{"language":"en","value":"{label}"}}}},"descriptions":{{"en":{{"language":"en","value":"{description}"}}}}}}'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            response = json.loads(result.stdout)
            
            # Check for success
            if 'success' in response and 'entity' in response:
                local_id = response['entity']['id'].replace('Q', '')
                log(f"Created entity {response['entity']['id']} with label: {label}")
                
                # Store QID mapping
                sql_query = f"INSERT INTO qid_mapping (local_id, original_qid) VALUES ({local_id}, '{qid}') ON DUPLICATE KEY UPDATE original_qid = '{qid}';"
                run_sql_query(sql_query)
                
                # Store in memory map too
                qid_map[qid] = response['entity']['id']
            else:
                log(f"Failed to import entity: {response}")
        except Exception as e:
            log(f"Error importing entity: {e}")
    
    # Sleep to avoid overloading the API
    time.sleep(1)

# Set up mapping table
setup_qid_mapping_table()

# Main processing
log("Starting to process the Wikidata dump file")

with gzip.open(dump_file, 'rt', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        
        # Process only English labels and descriptions
        label_match = label_pattern.match(line)
        description_match = description_pattern.match(line)
        
        if label_match:
            qid, label = label_match.groups()
            
            if qid not in entities:
                entities[qid] = create_entity(qid, label)
            else:
                entities[qid]["labels"]["en"] = {"language": "en", "value": label}
                
            processed_count += 1
            
        elif description_match:
            qid, description = description_match.groups()
            
            if qid not in entities:
                entities[qid] = create_entity(qid, None, description)
            else:
                entities[qid]["descriptions"]["en"] = {"language": "en", "value": description}
                
            processed_count += 1
        
        # Process in batches
        if len(entities) >= batch_size:
            batch_count += 1
            log(f"Processing batch {batch_count}, total processed: {processed_count}")
            import_entities_batch(entities)
            entities = {}
            
        # Check if we've reached the maximum number of entities to process
        if processed_count >= max_entities:
            break
            
# Process any remaining entities
if entities:
    batch_count += 1
    log(f"Processing final batch {batch_count}, total processed: {processed_count}")
    import_entities_batch(entities)

log(f"Completed importing {processed_count} entities in {batch_count} batches")
log(f"QID mappings stored in database 'qid_mapping' table")
EOL

# Copy the dump file to a location accessible by the container
echo "Preparing the dump file..." | tee -a $LOG_FILE
mkdir -p $DATA_ROOT_DIR/dumps
cp $DUMP_FILE $DATA_ROOT_DIR/dumps/latest-truthy.nt.gz

# Copy the Python script to the wikibase container
echo "Copying import script to the container..." | tee -a $LOG_FILE
docker compose exec -T wikibase mkdir -p /var/lib/mysql/dumps
docker compose cp $TEMP_DIR/import_wikidata.py wikibase:/var/lib/mysql/dumps/
docker compose exec -T wikibase chmod +x /var/lib/mysql/dumps/import_wikidata.py

# Install Python dependencies and run the import
echo "Starting the import process (this may take several hours)..." | tee -a $LOG_FILE
docker compose exec -T wikibase python3 -m pip install requests
docker compose exec -T wikibase python3 /var/lib/mysql/dumps/import_wikidata.py | tee -a $LOG_FILE

# Update search indexes after import
echo "Updating search indexes..." | tee -a $LOG_FILE
docker compose exec -T wikibase php /var/www/html/maintenance/rebuildall.php | tee -a $LOG_FILE

echo "Wikidata import process completed!" | tee -a $LOG_FILE
echo "Access your Wikibase instance at: http://localhost:8888" | tee -a $LOG_FILE
date | tee -a $LOG_FILE 