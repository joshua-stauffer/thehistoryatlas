# PyBroker
PyBroker is a wrapper library for aio-pika built for the History Atlas. It helps to enforce
standard connection, channel, exchange, and queue declarations and then exposes
hooks to register application level message handlers.

## Usage
### Initialize the Broker
PyBroker is designed to be used as a base class for an application's Broker module. After inheriting from the ```BrokerBase``` class, ensure the following parameters are passed  to the base class's init method:
- ```broker_username```
- ```broker_password```
- ```network_host_name```
- ```exchange_name```
- ```queue_name```      (defaults to an empty string "")

Across the History Atlas, the typical way to do this is to pass in a [tha-config](https://github.com/joshua-stauffer/thehistoryatlas/tree/dev/pylib/tha-config) instance and obtain the values from there:
```python
from pybroker import BrokerBase

class Broker(BrokerBase):

    def __init__(self, config):
        super().__init__(
            broker_username   = config.BROKER_USERNAME,
            broker_password   = config.BROKER_PASS,
            network_host_name = config.NETWORK_HOST_NAME,
            exchange_name     = config.EXCHANGE_NAME,
            queue_name        = config.QUEUE_NAME)
```
Note: the rest of this documentation assumes the perspective of this Broker subclass
### Register message handlers and callbacks
An application can receive messages on a given topic by using the async ```Broker.add_message_handler(routing_key, callback)``` method. The routing key is the topic string (for example ```query.readmodel``` or ```event.persisted```), and the callback is a function which will be invoked when the broker receives a message on that topic. 

### Callbacks
Callback functions should accept one parameter, which will be a binary string. Use the ```Broker.decode_message``` method (below) to transform into a dict. Internally, the callback function will be invoked inside a context manager which will automatically acknowledge the message after the callback returns. The context manager will also catch exceptions, in which case it will automatically reject the message. This allows the use of exceptions to conveniently communicate message processing errors back to the sender from any place in the application.

### Get Publishers
In order to create a stable publishing function, use the ```Broker.get_publisher(routing_key)``` hook. Invoking this method will return an async function which accepts a single parameter (a binary-encoded message) and will publish it to the predefined topic of routing_key.

Alternatively, use the ```Broker.publish_one(message, routing_key)``` method, which does exactly the same thing, but requires the routing key to be explicitly provided on each publish.

### Create and Decode Messages
```PyBroker.BrokerBase``` includes some utility methods for creating and decoding messages. 

```Broker.create_message()``` accepts the following parameters, and returns a Message object:
- body: dict (required)
- correlation_id: str 
- reply_to: str
- content_type: str
- expiration: int, float, datetime.datetime, or datetime.timedelta
- timestamp: int, float, datetime.datetime, or datetime.timedelta
- headers: dict

```Broker.decode_message()``` takes a binary message as a parameter and returns a dict. This is useful in callback methods passed to the ```add_message_handler``` method.

### Using AMQP Topics
When constructing topic strings, ```*``` can be used as a wildcard for exactly one word, and ```#``` can match zero or more words.

### Start the broker
Since starting the broker involves asynchronous network calls, it's not straightforward to implement the actual connection logic inside the init method. Instead, ```await``` the ```Broker.connect()``` method inside an asynchronous method on the user class. Across the application, this expected to be the ```Broker.start()``` method, and may implement any other useful startup logic, including registering message handlers and requesting history replays.

### Stop the broker
Use the ```Broker.cancel()``` method to unsubscribe from topic streams and disconnect from AMQP connection.