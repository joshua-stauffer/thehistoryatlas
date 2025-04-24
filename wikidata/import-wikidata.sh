#!/bin/bash
set -e

DUMP_FILE="/Volumes/seagate_hub/wikidata/data/data/temp/latest-truthy.nt.gz"
SAMPLE_DIR="/Volumes/seagate_hub/wikidata/data/data/temp/samples"
PROCESSED_DIR="/Volumes/seagate_hub/wikidata/data/data/temp/processed"
LOG_FILE="/Volumes/seagate_hub/wikidata/data/data/temp/import.log"
SAMPLE_SIZE=100  # Number of entities to process at once
WIKIBASE_URL="http://localhost:8888"
COOKIE_JAR="/Volumes/seagate_hub/wikidata/data/data/temp/cookies.txt"

# Create necessary directories
mkdir -p $SAMPLE_DIR $PROCESSED_DIR

echo "Starting Wikidata import process..." | tee -a $LOG_FILE
echo "Dump file: $DUMP_FILE" | tee -a $LOG_FILE

# Get login token and log in
get_login_token() {
    echo "Getting login token..." | tee -a $LOG_FILE
    LOGIN_TOKEN=$(curl -s -c $COOKIE_JAR "$WIKIBASE_URL/w/api.php?action=query&meta=tokens&type=login&format=json" | jq -r '.query.tokens.logintoken')
    echo "Login token: $LOGIN_TOKEN" | tee -a $LOG_FILE

    echo "Logging in..." | tee -a $LOG_FILE
    curl -s -b $COOKIE_JAR -c $COOKIE_JAR "$WIKIBASE_URL/w/api.php" \
        --data-urlencode "action=login" \
        --data-urlencode "lgname=admin" \
        --data-urlencode "lgpassword=wikiadmin123" \
        --data-urlencode "lgtoken=$LOGIN_TOKEN" \
        --data-urlencode "format=json" | tee -a $LOG_FILE
}

# Get CSRF token for edit operations
get_csrf_token() {
    echo "Getting CSRF token..." | tee -a $LOG_FILE
    CSRF_TOKEN=$(curl -s -b $COOKIE_JAR "$WIKIBASE_URL/w/api.php?action=query&meta=tokens&format=json" | jq -r '.query.tokens.csrftoken')
    echo "CSRF token: $CSRF_TOKEN" | tee -a $LOG_FILE
}

# Function to import an entity using the Wikibase API
import_entity() {
    local ENTITY_JSON=$1
    
    # Use curl to call the wbeditentity API with the token
    curl -s -b $COOKIE_JAR -X POST \
        -H "Content-Type: application/x-www-form-urlencoded" \
        --data-urlencode "action=wbeditentity" \
        --data-urlencode "format=json" \
        --data-urlencode "new=item" \
        --data-urlencode "data=$ENTITY_JSON" \
        --data-urlencode "token=$CSRF_TOKEN" \
        "$WIKIBASE_URL/w/api.php" | jq -c 'if has("error") then . else {success: true, id: .entity.id} end'
}

# Login and get token
get_login_token
get_csrf_token

# Process a batch of samples
process_batch() {
    local BATCH_NUM=$1
    local ENTITY_COUNT=0
    local SAMPLE_FILE="$SAMPLE_DIR/sample_$BATCH_NUM.nt"
    
    echo "Creating sample batch $BATCH_NUM..." | tee -a $LOG_FILE
    
    # Extract a sample of the data that contains English labels
    gunzip -c $DUMP_FILE | grep '@en' | head -n $SAMPLE_SIZE > $SAMPLE_FILE
    
    echo "Processing $SAMPLE_SIZE entities from batch $BATCH_NUM..." | tee -a $LOG_FILE
    
    # Process each line in the sample
    while IFS= read -r line; do
        # Extract subject, predicate, object from N-Triple line
        if [[ $line =~ \<([^>]+)\>\ \<([^>]+)\>\ \"([^\"]+)\"@en ]]; then
            SUBJECT="${BASH_REMATCH[1]}"
            PREDICATE="${BASH_REMATCH[2]}"
            OBJECT="${BASH_REMATCH[3]}"
            
            # Extract entity ID from subject URI
            ENTITY_ID=$(echo $SUBJECT | grep -o 'Q[0-9]\+')
            
            if [[ -n $ENTITY_ID ]]; then
                # Create JSON for this entity with English label
                ENTITY_JSON="{\"labels\":{\"en\":{\"language\":\"en\",\"value\":\"$OBJECT\"}}}"
                
                echo "Importing entity: $ENTITY_ID - $OBJECT" | tee -a $LOG_FILE
                RESULT=$(import_entity "$ENTITY_JSON")
                echo "Result: $RESULT" | tee -a $LOG_FILE
                
                ENTITY_COUNT=$((ENTITY_COUNT + 1))
            fi
        fi
    done < $SAMPLE_FILE
    
    echo "Completed batch $BATCH_NUM. Imported $ENTITY_COUNT entities." | tee -a $LOG_FILE
    
    # Move processed file to avoid reprocessing
    mv $SAMPLE_FILE $PROCESSED_DIR/
}

# Main import loop
BATCH_NUM=1
while [ $BATCH_NUM -le 10 ]; do  # Process 10 batches (adjust as needed)
    process_batch $BATCH_NUM
    BATCH_NUM=$((BATCH_NUM + 1))
done

echo "Rebuilding search index..." | tee -a $LOG_FILE
docker compose exec -T wikibase php /var/www/html/maintenance/rebuildall.php >> $LOG_FILE 2>&1

echo "Wikidata import process completed" | tee -a $LOG_FILE 