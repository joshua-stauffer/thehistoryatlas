# Event Store
The Event Store is the write-only path to the primary application database. For reading from the database, see the [History Service](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/history).

## I/O
- Listens to the ```events.emitted``` stream.
- After a successful commit to the database, publishes the new events to the ```events.persisted``` stream for public consumption across the backend.

## Contracts
The Event Store expects incoming messages on the ```events.emitted``` stream to be in the following form:
```typescript
{
    "type": "EVENT_TRANSACTION",
    "app_version":  string,
    "user":         string,
    "timestamp":    string,
    "payload": [
        <chronologically-ordered list of synthetic events, i.e. anything published on the event.persisted stream>
    ]
}
```
Published messages on the ```events.persisted``` stream will take the following form:
```typescript
{
    "type": "CITATION_ADDED",
    "transaction_guid": string,
    "app_version":      string,
    "user":             string,
    "timestamp":        string,
    "event_id":         int,
    "payload": {
        "text":         string,
        "tags":         string[],   # represents tag GUIDs
        "meta":         string      # represents meta GUID
    }
}
```
```typescript
{
    "type": "META_ADDED",
    "transaction_guid": string,
    "app_version":      string,
    "user":             string,
    "timestamp":        string,
    "event_id":         int,
    "payload": {
        "meta_guid":        string,
        "citation_guid":    string,
        "author":           string,
        "publisher":        string,
        "title":            string,
        "pub_date"?:        string,
        "page_num"?:        string,
        "url"?:             string,
        # Other arbitrary fields are permitted here
    }
}
```
```typescript
{
    "type": "PERSON_ADDED",
    "transaction_guid": string,
    "app_version":      string,
    "user":             string,
    "timestamp":        string,
    "event_id":         int,
    "payload": {
        "citation_guid":    string,
        "person_guid":      string,
        "person_name":      string,
        "citation_start":   int,
        "citation_end":     int,
    }
}
```
```typescript
{
    "type": "PERSON_TAGGED",
    "transaction_guid":   string,
    "app_version":        string,
    "user":               string,
    "timestamp":          string,
    "event_id":           int,
    "payload": {
        "citation_guid":    string,
        "person_guid":      string,
        "person_name":      string,
        "citation_start":   int,
        "citation_end":     int
    }
}
```
```typescript
{
    "type": "PLACE_ADDED",
    "transaction_guid": string,
    "app_version":      string,
    "user":             string,
    "timestamp":        string,
    "event_id":         int,
    "payload": {
        "citation_guid":    string,
        "place_guid":       string,
        "place_name":       string,
        "citation_start":   int,
        "citation_end":     int,
        "latitude":         float,
        "longitude":        float,
        # TODO: add geoshape string here
    }
}
```
```typescript
{
    "type": "PLACE_TAGGED",
    "transaction_guid":   string,
    "app_version":        string,
    "user":               string,
    "timestamp":          string,
    "event_id":           int,
    "payload": {
        "citation_guid":    string,
        "place_guid":       string,
        "place_name":       string,
        "citation_start":   int,
        "citation_end":     int,
    }
}
```
```typescript
{
    "type": "TIME_ADDED",
    "transaction_guid":   string,
    "app_version":        string,
    "user":               string,
    "timestamp":          string,
    "event_id":           int,
    "payload": {
        "citation_guid":    string,
        "time_guid":        string,
        "time_name":        string,
        "citation_start":   int,
        "citation_end":     int         
    }
}
```
```typescript
{
    "type": "TIME_TAGGED",
    "transaction_guid":   string,
    "app_version":        string,
    "user":               string,
    "timestamp":          string,
    "event_id":           int,
    "payload": {
        "citation_guid":    string,
        "time_guid":        string,
        "time_name":        string,
        "citation_start":   int,
        "citation_end":     int         
    }
}
```