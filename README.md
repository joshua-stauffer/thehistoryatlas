# The History Atlas

The History Atlas is a web application that stores scholarly citations correlating historical people with a time and place, and presents an interactive map searchable by time period, geographic area, or person.

The project has been my primary focus during my batch at [the Recurse Center](https://www.recurse.com), a three month self-directed retreat for programmers in NYC from April-June 2021.

I've been building the History Atlas with a CQRS/Event-Sourcing architecture in mind. The goal is to have a flexible, extensible base infrastructure that will be easy to maintain and scale, and will allow for significant changes in the frontend data requirements without needing to make changes to the primary database.

The project is built as a series of microservices which communicate asynchronously via RabbitMQ. Details on message contracts between services are found in each application's documentation.

## Overview
### Core Services
- [Client](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/client): React app
- [API:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/api) Apollo GraphQL service
- [Read Model:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/readmodel) Service for querying application state
- [Write Model:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/writemodel) Service for making mutations to application state
- [Event Store:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/eventstore) Canonical database for the application
### Supporting Services
- [History Service:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/history) provides an event stream of the canonical database for building local state
- [PyBroker:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/pylib/pybroker) Base library for Python AMQP brokers across the application
- [NLP Service:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/nlp) Natural language processing service providing custom named entity recognition (NER)
- [Geo Service:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/geo) Database of place names and their geographic coordinates.
- [tha-config:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/pylib/tha-config) Basic config library for working with environmental variables across Python services
- [Tackle:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/testlib/tackle) Integration testing library built to help ensure message contracts between services
- [Builder:](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/builder) Series of scripts to generate and manage data in development:
  - [builddata](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/builddata.py): a command-line tool to create annotations of real data sources
  - [build_geo_src](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/build_geo_src.py): sources geo data from geonames.org and saves it to disk for the use by other scripts.
  - [build_fake_data](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/build_fake_data.py): a script to generate a large amount of fake (but realistically interconnected) related data.
  - [mock_client](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/mockclient.py): a tool to programmatically publish data from json files to the GraphQL API endpoint.
- [User Accounts Service](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/accounts): Manages user information
- Email Service: Provides email services across the application (in progress)
- Logging Service: Tracks query/response times and application traffic patterns (in progress)

## Local project setup
- [install/setup docker](https://docs.docker.com/get-docker/)
- fork/clone the repo, and navigate to the project root directory
- Build the project with ``` sudo bash build.sh```
- Run the project with ``` docker-compose up```
- Generate fake data (or create your own real data) and publish it to the application using the scripts in the [builder](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/builder) directory.
- Stop the project with ctl-C in the same terminal or with ```docker-compose down``` in a separate tab.

The RabbitMQ admin console is available at [localhost:15672](http://localhost:15672).
- username: guest
- password: guest
The GraphQL API is available at [localhost:4000](http://localhost:4000).

### First Time Build Considerations
On the first build, the Geo service will build its database, which involves pulling in data from geonames.org and building a graph database structure locally. The source for this build can be adjusted in the docker compose file under the Geo service. The default source is cities15000.zip, which will take ~10-15 minutes to fully build. The alternate source (cities500.zip) will be used in production, but takes ~3.5 hours to build, so use at your own risk.

### Tests
Tests can be run with the ```bash test.sh``` command.

### Contributing
Ideas, suggestions, and contributions are all welcome! If you would like to be involved, the [issues page](https://github.com/joshua-stauffer/thehistoryatlas/issues) is a great place to start, but feel free to reach out directly as well.

### Building on Apple silicon (ARM64)
At the time of writing, there are still some lingering issues with building select libraries on Apple silicon (notably, numpy, which is a dependency for spaCy in the NLP app). If you are developing on an ARM64 architecture, rename the default docker file [in the NLP directory](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/nlp) to something else, and rename the Dockerfile_arm64 file to simply Dockerfile. This alternate dockerfile uses Conda as a workaround, but has caused problems on Linux machines, so is no longer the default build.
