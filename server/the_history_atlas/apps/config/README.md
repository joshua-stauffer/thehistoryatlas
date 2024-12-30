# THA-Config
THA-Config is a small library which streamlines handling environmental variables across the History Atlas. 
## Usage
On creation of a new instance of the ```Config``` class, tha-config searches the local environment for the following variables:
- DEBUG
- TESTING
- PROD_DB_URI
- DEV_DB_URI
- CONFIG  
- HOST_NAME
- BROKER_USERNAME
- BROKER_PASS
- QUEUE_NAME
- EXCHANGE_NAME


After initialization, the following properties are available on the ```Config``` object:
- TESTING
- CONFIG
  - 'PRODUCTION' or 'DEVELOPMENT'
- DB_URI
  - TESTING is truthy? => in memory sqlite database, else:
  - CONFIG is PRODUCTION? => PROD_DB_URI, else:
  - DEV_DB_URI
- NETWORK_HOST_NAME
- BROKER_USERNAME
- BROKER_PASS
- QUEUE_NAME
- EXCHANGE_NAME

## Extension
Individual apps are free to extend the Config class by adding whatever specific env variables they need to access ([example](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/history/app/history_config.py)).