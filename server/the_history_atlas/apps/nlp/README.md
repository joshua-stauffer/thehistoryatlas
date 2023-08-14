# NLP Service
The NLP Service searches user provided text for people, places, and times using the [spaCy library](https://spacy.io) and a custom trained NER. After extracting entities from the text, the service resolves them in parallel against the Read Model for known GUIDs, and the Geo Service for place coordinates and geoshapes. Upon receipt of both of these subqueries, it returns a response to the client.

## I/O
- Listens to ```query.nlp```, and publishes responses to the ```reply_to``` field provided by the client.
- Listens to ```signal.nlp.train```, and upon receipt of a message, retrains model based on the latest data. See [rebuilding the model](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/nlp#rebuilding-model), below.

## Contracts
The NLP Service requires incoming messages on the ```query.nlp``` stream to have two properties defined:
- ```reply_to```: queue to receive query response
- ```correlation_id```: query GUID

Messages have the following shape:
```typescript
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
                    "geo_shape"?:    string
                }
            }[],
        }
    }
}
```

## Building the Model
The NLP service now ships with a prebuilt custom-trained NER model, so there's no need for an initial build.

## Rebuilding Model
A rebuild of the spaCy model can be triggered by sending a blank message to the ```signal.nlp.train``` topic. Note that this will effectively take the service offline for an extended period of time -- currently, close to 24 hours.

## Memory Usage
The NLP Service uses a significant amount of memory, and can cause crashes by exceeding the default 2 GB of RAM allocated by Docker. If 137 Errors are encountered in development, the solution is to increase that limit in the Docker settings. If RAM isn't in shortage, I recommend allowing at least 4 GB for good performance.
