# Write Model
The Write Model is tasked with transforming ```Commands``` capturing user intent into ```Events``` to be persisted into the canonical database.

## Validation
One of the primary roles of the Write Model is to ensure that the data which reaches the Event Store is valid. Current validations include making sure each citation text is unique (excluding whitespace and punctuation), checking that GUIDs are of the correct type (i.e. a Person GUID can't be given to a Place tag), and making sure that all required command fields are present. 

## Eventual Consistency Woes
One difficulty associated with a distributed system is that there is only the promise of eventual consistency -- since the local validation database is built from the ```events.persisted``` stream, there will be a delay between emitting a new event and receiving it back in the form of a persisted event. This could be a problem in scenarios like duplicate commands -- if they arrive nearly simultaneously, the first command being validated wouldn't necessarily be fast enough for the second to be rejected. To address this issue, [the Write Model implements a Short Term Memory as a part of its database layer](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/writemodel/app/state_manager/database.py), and for a short period treats Events it has emitted as if they were persisted. Of course, this could be a problem if the Emitted Event never reaches the Event Store and the user wishes to immediately retry the Command, but this is a short term problem that is acceptable for the purposes of this application. Part of this design decision is based on the observation that there is more that can go wrong between the client and the Write Model than between the Write Model and the Event Store.

## I/O
- Listens to the ```commands.writemodel``` stream.
- Publishes to the ```events.emitted``` stream.
- Listens to the ```events.persisted``` stream to build validation database.

## Contracts
The Write Model expects incoming messages on the ```query.readmodel``` stream to have the following shape:
```json
{
    "type": "PUBLISH_NEW_CITATION",
    "user":         string,
    "timestamp":    string,
    "app_version":  string,
    "
    "payload": {
        "text": string,
        "GUID": string,     # citation GUID
        "tags": {
            "type":             enum PERSON, PLACE, TIME,
            "GUID":         string,
            "start_char":   int,
            "stop_char":    int,
            "name":         string,
            "latitude"?:    float,          # PLACE tags only
            "longitude"?:   float,          # |
            "geoshape"?:    string          # |
        }[],
        "meta": {
            "author":       string,
            "publisher":    string,
            "title":        string
            # other arbitrary fields are accepted
        },
    }
}
```
