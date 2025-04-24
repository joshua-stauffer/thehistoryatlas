#!/bin/bash
set -e

DUMP_FILE="/Volumes/seagate_hub/wikidata/data/data/temp/latest-truthy.nt.gz"
DATA_ROOT_DIR="/Volumes/seagate_hub/wikidata/data/data"
LOG_FILE="$DATA_ROOT_DIR/import_full.log"
WIKIBASE_URL="http://localhost:8888"
TEMP_DIR="$DATA_ROOT_DIR/temp/processing"
BATCH_SIZE=100

# Create necessary directories
mkdir -p $TEMP_DIR
mkdir -p $DATA_ROOT_DIR/dumps

echo "Starting Wikidata import process..." | tee -a $LOG_FILE
date | tee -a $LOG_FILE

# Make sure the containers are running
echo "Ensuring all containers are running..." | tee -a $LOG_FILE
docker compose up -d

# Wait for services to be ready
echo "Waiting for services to be fully ready (60 seconds)..." | tee -a $LOG_FILE
sleep 60

# Copy the Wikidata dump
echo "Copying Wikidata dump to the container..." | tee -a $LOG_FILE
cp $DUMP_FILE $DATA_ROOT_DIR/dumps/latest-truthy.nt.gz

# Create a script to process and import Wikidata entities
echo "Creating processing scripts..." | tee -a $LOG_FILE

# 1. Extract and prepare data
cat > $TEMP_DIR/extract_entities.sh << 'EOL'
#!/bin/bash
DUMP_FILE="/var/lib/mysql/dumps/latest-truthy.nt.gz"
OUTPUT_DIR="/var/lib/mysql/dumps/entities"
LOG_FILE="/var/lib/mysql/dumps/import.log"
BATCH_SIZE=100

mkdir -p $OUTPUT_DIR

echo "Starting entity extraction..." > $LOG_FILE

# Extract English labels and descriptions
echo "Extracting English labels..." >> $LOG_FILE
zcat $DUMP_FILE | grep '<http://www.w3.org/2000/01/rdf-schema#label> ".*"@en' > $OUTPUT_DIR/labels.nt

echo "Extracting English descriptions..." >> $LOG_FILE
zcat $DUMP_FILE | grep '<http://schema.org/description> ".*"@en' > $OUTPUT_DIR/descriptions.nt

echo "Processing entities into batches..." >> $LOG_FILE

# Function to create JSON for an entity
create_entity_json() {
    local QID=$1
    local LABEL=$2
    local DESCRIPTION=$3
    
    # Create proper JSON with escaping
    LABEL=$(echo "$LABEL" | sed 's/"/\\"/g')
    DESCRIPTION=$(echo "$DESCRIPTION" | sed 's/"/\\"/g')
    
    echo "{\"labels\":{\"en\":{\"language\":\"en\",\"value\":\"$LABEL\"}},\"descriptions\":{\"en\":{\"language\":\"en\",\"value\":\"$DESCRIPTION\"}}}"
}

# Process files
declare -A ENTITIES
COUNT=0
BATCH=1

# Process labels
while IFS= read -r line; do
    if [[ $line =~ \<http://www.wikidata.org/entity/(Q[0-9]+)\>\ \<http://www.w3.org/2000/01/rdf-schema#label\>\ \"(.*)\"@en ]]; then
        QID="${BASH_REMATCH[1]}"
        LABEL="${BASH_REMATCH[2]}"
        
        if [[ -z ${ENTITIES[$QID]} ]]; then
            ENTITIES[$QID]="$QID|||$LABEL|||"
        else
            LABEL_DESC=${ENTITIES[$QID]}
            ENTITIES[$QID]="${LABEL_DESC%|||*}|||$LABEL|||${LABEL_DESC##*|||}"
        fi
        
        COUNT=$((COUNT + 1))
        
        # If we've reached the batch size, write to file
        if [ $COUNT -ge $BATCH_SIZE ]; then
            echo "Writing batch $BATCH with $COUNT entities..." >> $LOG_FILE
            
            # Write each entity to a batch file
            for key in "${!ENTITIES[@]}"; do
                IFS="|||" read -r ENTITY_QID ENTITY_LABEL ENTITY_DESC <<< "${ENTITIES[$key]}"
                JSON=$(create_entity_json "$ENTITY_QID" "$ENTITY_LABEL" "$ENTITY_DESC")
                echo "$ENTITY_QID $JSON" >> "$OUTPUT_DIR/batch_$BATCH.json"
            done
            
            # Reset counter and increment batch
            COUNT=0
            BATCH=$((BATCH + 1))
            unset ENTITIES
            declare -A ENTITIES
        fi
    fi
done < $OUTPUT_DIR/labels.nt

# Process descriptions
while IFS= read -r line; do
    if [[ $line =~ \<http://www.wikidata.org/entity/(Q[0-9]+)\>\ \<http://schema.org/description\>\ \"(.*)\"@en ]]; then
        QID="${BASH_REMATCH[1]}"
        DESCRIPTION="${BASH_REMATCH[2]}"
        
        if [[ -z ${ENTITIES[$QID]} ]]; then
            ENTITIES[$QID]="$QID||||||$DESCRIPTION"
        else
            LABEL_DESC=${ENTITIES[$QID]}
            ENTITIES[$QID]="${LABEL_DESC%|||*}|||${LABEL_DESC#*|||*}$DESCRIPTION"
        fi
        
        COUNT=$((COUNT + 1))
        
        # If we've reached the batch size, write to file
        if [ $COUNT -ge $BATCH_SIZE ]; then
            echo "Writing batch $BATCH with $COUNT entities..." >> $LOG_FILE
            
            # Write each entity to a batch file
            for key in "${!ENTITIES[@]}"; do
                IFS="|||" read -r ENTITY_QID ENTITY_LABEL ENTITY_DESC <<< "${ENTITIES[$key]}"
                JSON=$(create_entity_json "$ENTITY_QID" "$ENTITY_LABEL" "$ENTITY_DESC")
                echo "$ENTITY_QID $JSON" >> "$OUTPUT_DIR/batch_$BATCH.json"
            done
            
            # Reset counter and increment batch
            COUNT=0
            BATCH=$((BATCH + 1))
            unset ENTITIES
            declare -A ENTITIES
        fi
    fi
done < $OUTPUT_DIR/descriptions.nt

# Write any remaining entities
if [ $COUNT -gt 0 ]; then
    echo "Writing final batch $BATCH with $COUNT entities..." >> $LOG_FILE
    
    # Write each entity to a batch file
    for key in "${!ENTITIES[@]}"; do
        IFS="|||" read -r ENTITY_QID ENTITY_LABEL ENTITY_DESC <<< "${ENTITIES[$key]}"
        JSON=$(create_entity_json "$ENTITY_QID" "$ENTITY_LABEL" "$ENTITY_DESC")
        echo "$ENTITY_QID $JSON" >> "$OUTPUT_DIR/batch_$BATCH.json"
    done
fi

echo "Total batches created: $BATCH" >> $LOG_FILE
echo "Entity extraction and preparation completed" >> $LOG_FILE
EOL

# 2. Import script using curl and cookies directly
cat > $TEMP_DIR/import_entities.sh << 'EOL'
#!/bin/bash
ENTITIES_DIR="/var/lib/mysql/dumps/entities"
LOG_FILE="/var/lib/mysql/dumps/import.log"
COOKIE_JAR="/var/lib/mysql/dumps/cookies.txt"
API_URL="http://localhost/w/api.php"
DB_NAME="wikidata"
DB_USER="root"
DB_PASS="wikidataroot"

# Set up QID mapping table
echo "Setting up QID mapping table..." >> $LOG_FILE
mysql -h localhost -u $DB_USER -p$DB_PASS $DB_NAME -e "
CREATE TABLE IF NOT EXISTS qid_mapping (
    local_id INT NOT NULL,
    original_qid VARCHAR(20) NOT NULL,
    PRIMARY KEY (local_id),
    UNIQUE KEY (original_qid)
);
"

# Login and get tokens
echo "Logging in to Wikibase..." >> $LOG_FILE

# Get login token
echo "Getting login token..." >> $LOG_FILE
LOGIN_TOKEN=$(curl -s -c $COOKIE_JAR "$API_URL?action=query&meta=tokens&type=login&format=json" | grep -o '"logintoken":"[^"]*"' | cut -d'"' -f4)
echo "Login token obtained" >> $LOG_FILE

# Login
echo "Logging in as admin..." >> $LOG_FILE
curl -s -b $COOKIE_JAR -c $COOKIE_JAR "$API_URL" \
    --data-urlencode "action=login" \
    --data-urlencode "lgname=admin" \
    --data-urlencode "lgpassword=wikiadmin123" \
    --data-urlencode "lgtoken=$LOGIN_TOKEN" \
    --data-urlencode "format=json" \
    -o /dev/null

# Get CSRF token
echo "Getting CSRF token..." >> $LOG_FILE
CSRF_TOKEN=$(curl -s -b $COOKIE_JAR "$API_URL?action=query&meta=tokens&format=json" | grep -o '"csrftoken":"[^"]*"' | cut -d'"' -f4)
echo "CSRF token obtained: ${CSRF_TOKEN:0:5}..." >> $LOG_FILE

# Process each batch file
TOTAL_IMPORTED=0
for BATCH_FILE in $(ls $ENTITIES_DIR/batch_*.json 2>/dev/null); do
    BATCH_NUM=$(basename $BATCH_FILE | sed 's/batch_\([0-9]*\).json/\1/')
    echo "Processing batch $BATCH_NUM..." >> $LOG_FILE
    
    # Read and process each line
    while IFS=' ' read -r QID JSON; do
        # Create the entity
        RESPONSE=$(curl -s -b $COOKIE_JAR "$API_URL" \
            --data-urlencode "action=wbeditentity" \
            --data-urlencode "format=json" \
            --data-urlencode "new=item" \
            --data-urlencode "data=$JSON" \
            --data-urlencode "token=$CSRF_TOKEN")
        
        # Check for success
        if echo "$RESPONSE" | grep -q '"success":1'; then
            # Extract entity ID
            LOCAL_ID=$(echo "$RESPONSE" | grep -o '"id":"Q[0-9]*"' | cut -d'"' -f4 | sed 's/Q//')
            
            if [ -n "$LOCAL_ID" ]; then
                # Store the mapping
                mysql -h localhost -u $DB_USER -p$DB_PASS $DB_NAME -e "
                INSERT INTO qid_mapping (local_id, original_qid) 
                VALUES ($LOCAL_ID, '$QID') 
                ON DUPLICATE KEY UPDATE original_qid = '$QID';
                "
                echo "Created entity with local ID Q$LOCAL_ID for Wikidata $QID" >> $LOG_FILE
                TOTAL_IMPORTED=$((TOTAL_IMPORTED + 1))
            else
                echo "Failed to extract local ID for $QID: $RESPONSE" >> $LOG_FILE
            fi
        else
            if echo "$RESPONSE" | grep -q '"code":"badtoken"'; then
                echo "Bad token. Getting a new CSRF token..." >> $LOG_FILE
                CSRF_TOKEN=$(curl -s -b $COOKIE_JAR "$API_URL?action=query&meta=tokens&format=json" | grep -o '"csrftoken":"[^"]*"' | cut -d'"' -f4)
                echo "New CSRF token obtained: ${CSRF_TOKEN:0:5}..." >> $LOG_FILE
                # Retry with new token
                RESPONSE=$(curl -s -b $COOKIE_JAR "$API_URL" \
                    --data-urlencode "action=wbeditentity" \
                    --data-urlencode "format=json" \
                    --data-urlencode "new=item" \
                    --data-urlencode "data=$JSON" \
                    --data-urlencode "token=$CSRF_TOKEN")
                
                if echo "$RESPONSE" | grep -q '"success":1'; then
                    # Extract entity ID
                    LOCAL_ID=$(echo "$RESPONSE" | grep -o '"id":"Q[0-9]*"' | cut -d'"' -f4 | sed 's/Q//')
                    
                    if [ -n "$LOCAL_ID" ]; then
                        # Store the mapping
                        mysql -h localhost -u $DB_USER -p$DB_PASS $DB_NAME -e "
                        INSERT INTO qid_mapping (local_id, original_qid) 
                        VALUES ($LOCAL_ID, '$QID') 
                        ON DUPLICATE KEY UPDATE original_qid = '$QID';
                        "
                        echo "Created entity with local ID Q$LOCAL_ID for Wikidata $QID" >> $LOG_FILE
                        TOTAL_IMPORTED=$((TOTAL_IMPORTED + 1))
                    else
                        echo "Failed to extract local ID for $QID: $RESPONSE" >> $LOG_FILE
                    fi
                else
                    echo "Failed to create entity for $QID: $RESPONSE" >> $LOG_FILE
                fi
            else
                echo "Failed to create entity for $QID: $RESPONSE" >> $LOG_FILE
            fi
        fi
        
        # Small delay to avoid overwhelming the API
        sleep 0.5
    done < $BATCH_FILE
    
    echo "Completed batch $BATCH_NUM" >> $LOG_FILE
    echo "Total entities imported so far: $TOTAL_IMPORTED" >> $LOG_FILE
    
    # Refresh token every 5 batches
    if [ $((BATCH_NUM % 5)) -eq 0 ]; then
        echo "Refreshing CSRF token..." >> $LOG_FILE
        CSRF_TOKEN=$(curl -s -b $COOKIE_JAR "$API_URL?action=query&meta=tokens&format=json" | grep -o '"csrftoken":"[^"]*"' | cut -d'"' -f4)
        echo "New CSRF token obtained: ${CSRF_TOKEN:0:5}..." >> $LOG_FILE
    fi
done

echo "Import process completed. Total entities imported: $TOTAL_IMPORTED" >> $LOG_FILE
EOL

# Make scripts executable
echo "Preparing container for import..." | tee -a $LOG_FILE
docker compose exec -T wikibase mkdir -p /var/lib/mysql/dumps/entities
docker compose cp $TEMP_DIR/extract_entities.sh wikibase:/var/lib/mysql/dumps/
docker compose cp $TEMP_DIR/import_entities.sh wikibase:/var/lib/mysql/dumps/
docker compose exec -T wikibase chmod +x /var/lib/mysql/dumps/extract_entities.sh
docker compose exec -T wikibase chmod +x /var/lib/mysql/dumps/import_entities.sh

# Extract entities first
echo "Extracting entities from the Wikidata dump (this may take a while)..." | tee -a $LOG_FILE
docker compose exec -T wikibase bash /var/lib/mysql/dumps/extract_entities.sh

# Import entities
echo "Importing entities into Wikibase (this will take several hours)..." | tee -a $LOG_FILE
docker compose exec -T wikibase bash /var/lib/mysql/dumps/import_entities.sh

# Update search indexes after import
echo "Updating search indexes..." | tee -a $LOG_FILE
docker compose exec -T wikibase php /var/www/html/maintenance/rebuildall.php

# Add a view to query entities by original Wikidata ID
echo "Creating view for querying entities by Wikidata ID..." | tee -a $LOG_FILE
docker compose exec -T wikibase mysql -h localhost -u root -pwikidataroot wikidata -e "
CREATE OR REPLACE VIEW wikidata_entities AS
SELECT 
    CONCAT('Q', qm.local_id) AS local_entity_id,
    qm.original_qid AS wikidata_id,
    pl.page_title AS entity_title
FROM 
    qid_mapping qm
JOIN 
    page pl ON CONCAT('Q', qm.local_id) = pl.page_title
WHERE 
    pl.page_namespace = 0;
"

echo "Wikidata import process completed!" | tee -a $LOG_FILE
echo "Access your Wikibase instance at: http://localhost:8888" | tee -a $LOG_FILE
echo "Query Service UI available at: http://localhost:8834" | tee -a $LOG_FILE
date | tee -a $LOG_FILE 