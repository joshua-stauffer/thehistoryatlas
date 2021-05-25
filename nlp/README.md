# NLP Service
The NLP Service searches user provided text for people, places, and times using the [spaCy library](https://spacy.io) and a custom trained NER. After extracting entities from the text, the service resolves them in parallel against the Read Model for known GUIDs, and the Geo Service for place coordinates and geoshapes. Upon receipt of both of these subqueries, it returns a response to the client.

## I/O
- Listens to ```query.nlp```, and publishes responses to the ```reply_to``` field provided by the client.
- Listens to ```signal.nlp.train```, and upon receipt of a message, retrains model based on the latest data. Note that this will effectively take the service offline for an extended period of time -- currently, close to 24 hours. See 'building the model' for more details.

## Contracts
The Geo Service requires incoming messages on the ```query.nlp``` stream to have two properties defined:
- ```reply_to```: queue to receive query response
- ```correlation_id```: query GUID

Messages have the following shape:
```json
# Query
{
    "type": "PROCESS_TEXT",
    "payload": {
        "text":     string
    }
}

# Response
{
    "type": "TEXT_PROCESSED",
    "payload": {
        "text":     string,
        "text_map": {
            "PERSON": {
                "start_char":   int,
                "stop_char":    int,
                "text":         string,
                "GUID":         string[],
            }[],
            "PLACE": {
                "start_char":   int,
                "stop_char":    int,
                "text":         string,
                "GUID":         string[],
            }[],
            "TIME": {
                "start_char":   int,
                "stop_char":    int,
                "text":         string,
                "GUID":         string[],
                "coords": {
                    "latitude":     float,
                    "longitude":    float,
                    "geoshape"?:    string
                }
            }[],
        }
    }
}
```

## Building the Model
The NLP service requires a spaCy model in order to perform NER. This is a large file, and so doesn't ship with the application. Instead, it will be built the first time the service is started, and saved in a volume for future use. Please note that due to the limited resources available in a Docker instance, this build currently takes around 24 hours. It's fine to interrupt the service early, and as long as it's completed the first epoch, a model will be available. When the application is up, you can check if the model has built yet by discovering it's container ID with ```docker ps```, then entering the container with a shell with ```docker exec -it <container id> bash``` and looking in the ```models``` directory. If a ```model-best``` directory exists, it should be okay to interrupt the training process, although the NER will likely return weaker results.


## Rebuilding Model
A rebuild of the spaCy model can be triggered by sending a blank message to the ```signal.nlp.train``` topic.

## Memory Usage
The NLP Service uses a significant amount of memory, and can cause crashes by exceeding the default 2 GB of RAM allocated by Docker. If 137 Errors are encountered in development, the solution is to increase that limit in the Docker settings. If RAM isn't in shortage, I recommend allowing at least 4 GB for good performance.

## Build Without NLP
In case these performance issues are unworkable, the NLP service can be commented out of the docker-compose file, and the rest of the application will continue to work just fine. 