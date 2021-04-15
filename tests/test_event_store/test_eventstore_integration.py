"""
This integration test sets up mock components to integrate with the Event Store.
Results are printed to the terminal:
    Emitted Event Entered
    Persisted Event Returned


WARNING!
This container publishes events to the EventStore. If EventStore is not running with
the env variable Testing=True, it will write to the current database. Ensure that the
EventStore container is running in Testing mode before running this test.
"""

import os
import json
import pika
from config import Config

class MockProducer:
    """Represents the WriteModel.
    Publishes to the Event Store's emitted_events exchange"""

    def __init__(self):
        self.config = Config()

        # declare connection and channel
        # TODO: update to use the login variables passed from config
        self.conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config.NETWORK_HOST_NAME,
                # virtual_host='test'
                )
        )
        self.channel = self.conn.channel()

        # declare exchange
        self.channel.exchange_declare(
            exchange='emitted_events',
            exchange_type='direct'
        )

        # declare queues
        self.channel.queue_declare(
            self.config.RECV_QUEUE,
            durable=True,
            auto_delete=False
        )
        self.channel.queue_bind(
            exchange='emitted_events',
            queue=self.config.RECV_QUEUE
        )

    def send_msg(self, msg):
        self.channel.basic_publish(
            exchange='emitted_events',
            routing_key=self.config.RECV_QUEUE,
            body=msg
        )

    def shutdown(self):
        self.conn.close()

class MockConsumer:
    """Represents recipients from the Event Store's fanout exchange.

    Create multiple instances to test receiving the same message
    across multiple services.
    """

    def __init__(self, queue_name):
        self.config = Config()
        self.queue_name = queue_name

        # declare connection and channel
        credentials = pika.PlainCredentials(
            self.config.BROKER_USERNAME,
            self.config.BROKER_PASS
        )
        self.conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config.NETWORK_HOST_NAME,
                credentials=credentials,
                # virtual_host='test'
            )
        )
        self.channel = self.conn.channel()

        # declare exchanges
        self.channel.exchange_declare(
            exchange='persisted_events',
            exchange_type='fanout'
        )

        # declare queue
        result = self.channel.queue_declare(
            self.queue_name,
            durable=True,
            auto_delete=False
        )

        self.channel.queue_bind(
            exchange='persisted_events',
            queue=result.method.queue
        )

        self.inbox = None

    def get_msgs(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._recv
        )
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.shutdown()

    def _recv(self, ch, method_frame, properties, body):
        self.inbox = body
        ch.basic_ack(delivery_tag=method_frame.delivery_tag)
        raise KeyboardInterrupt()

    def shutdown(self):
        self.conn.close()


def test_event_added():
    """Creates producers and consumers, passes an event to the producer,
    then checks consumers to ensure deliver.
    
    Requires that the Event Store and RabbitMQ are up and running in
    separate containers, and the necessary env variables are set.
    """
    producer = MockProducer()
    read_consumer = MockConsumer('read')
    write_consumer = MockConsumer('write')
    msg = json.dumps({
        'type': 'PersonAdded',
        'timestamp': 'now!',
        'user': 'test_user',
        'payload': {
            'name': 'frederick the great'
        },
        'priority': 1
    })
    producer.send_msg(msg)
    read_consumer.get_msgs()
    write_consumer.get_msgs()
    spacer = '\n\n'
    print('_' * 79 + spacer)
    print('Tested PersonAdded')
    print('Event Store Input: ', json.loads(msg))
    print('Write Model Output: ', json.loads(write_consumer.inbox.decode()))
    print('Read Model Output: ', json.loads(read_consumer.inbox.decode()))
    print(spacer)

if __name__ == "__main__":
    test_event_added()
