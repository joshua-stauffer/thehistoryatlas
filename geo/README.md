# Geo Service
The Geo Service maintains a database of place names and coordinates to and provides query access to other services across the application. Geo data is programmatically pulled in from [geonames.org](https://www.geonames.org) on the first time the application is built.

## I/O
- Listens to the ```query.geo``` stream, and publishes responses to the ```reply_to``` field provided by the client.

## Contracts
The Geo Service requires incoming messages on the ```query.geo``` stream to have two properties defined:
- ```reply_to```: queue to receive query response
- ```correlation_id```: query GUID

Resolve a name into a list of coordinates, if any exist:
```json
# Query
{
    "type": "GET_COORDS_BY_NAME",
    "payload": {
        "name": string
    }
}

# Response
{
    "type": "COORDS_BY_NAME",
    "payload": {
        "coords": {
            <name> : {
                "latitude":     float,
                "longitude":    float,
                "geoshape":     string
            }[]
        }
    }
}
```
Similarly, resolve a list of names into coordinates:
```json
# Query
{
    "type": "GET_COORDS_BY_NAME_BATCH",
    "payload": {
        "names": string[]
    }
}

# Response
{
    "type": "COORDS_BY_NAME_BATCH",
    "payload": {
        "coords": {
            <name> : {
                "latitude":     float,
                "longitude":    float,
                "geoshape":     string
            }[]
        }
    }
}
```
