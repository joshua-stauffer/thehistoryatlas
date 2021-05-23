# The History Atlas

The History Atlas is a web application that stores scholarly citations correlating historical people with a time and place, and presents an interactive map searchable by time period, geographic area, or person.

The project has been my primary focus during my batch at [the Recurse Center](https://www.recurse.com), a three month self-directed retreat for programmers in NYC from April-June 2021. It's still very much a work in progress -- you can see the latest status of individual components in the [TODO file](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/todo). 

I've been building the History Atlas with a CQRS/Event-Sourcing architecture in mind. The goal is to have a flexible, extensible base infrastructure that will be easy to maintain and scale, and will allow for significant changes in the frontend data requirements without needing to make changes to the primary database. In preparation for this project [I built a non-distributed, synchronous Todo application with a similar architecture](https://github.com/joshua-stauffer/EventBullet) -- the basic flow of data is the same in the History Atlas, without the complications of asynchronicity, so could potentially be a helpful resource.

The project is built as a series of microservices which communicate asynchronously via RabbitMQ. Details on message contracts between services are found in the [api.txt file](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/api.txt)

## Local project setup
- [install/setup docker](https://docs.docker.com/get-docker/)
- fork/clone the repo, and navigate to the project root directory
- Build the project with ``` bash build.sh```
- Run the project with ``` docker-compose up```
- Stop the project with ctl-C in the same terminal or with```docker-compose down``` in a separate tab.

The RabbitMQ admin console is available at [localhost:15672](http://localhost:15672).
- username: guest
- password: guest
The GraphQL API is available at [localhost:4000](http://localhost:4000).

### Extra considerations for the Natural Language Processing service
On the first build, the NLP service will need to build a model from the included training data. This will take a long time due to the limited resources allocated by default to a docker instance: on my machine ~24 hours. An optimization is currently in the works, but if you have an idea for making this more efficient, please reach out! After the first build, the model will be stored in a docker volume, so rebuilding won't be necessary unless the docker volume is removed. Rebuilds can be requested manually by sending an message in the main exchange to the RabbitMQ routing key 'signal.nlp.train'. The NLP service can consume a significant amount of memory as well, so it's recommended to increase Docker's memory allowance to around 4 gigs, if possible, to avoid 137 errors. In case these considerations make running the full application difficult, the NLP service can be commented out in the docker-compose file, and other functionality will continue to work. The training can also be cut short, and as long as the first batch has processed, the application will have a model to work with.

### Tests
Tests can be run with the ```bash test.sh``` command.

### Contributing
Ideas, suggestions, and contributions are all welcome!