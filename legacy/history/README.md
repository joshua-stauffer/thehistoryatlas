# History Service
The History Service is the read-only path to the primary application database. For writing to the database, see the [Event Store](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/eventstore).

## I/O
- Listens to the ```event.replay.request``` stream.
- Publishes exclusively to the queue given by incoming replay requests, defined under the ```reply_to``` property, by convention ```event.replay.<service name>```

## Contracts
The History service requires incoming messages on the ```event.replay.request``` stream to have two properties defined:
- ```reply_to```: queue to receive message replay stream
- ```correlation_id```: GUID used to prevent duplicate replay requests.

Additionally, client should provide the ID of the last event they've received (default of 0), and the History service will begin replay from the next event in the sequence.
```typescript
{
    "type": "REQUEST_HISTORY_REPLAY",
    "payload":{
        "last_event_id":    int
    }
}
```
Outgoing messages on the ```event.replay.<service name>``` stream will take exactly the same form as when the event was originally published on the ```event.persisted``` stream ([see documentation here](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/eventstore/README.md#Contracts)).
