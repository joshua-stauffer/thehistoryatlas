"""
This integration test sets up mock components to integrate with the Event Store.
Results are printed to the terminal:
    Emitted Event Entered
    Persisted Event Returned
"""

import os
import json
import pika
from config import Config

class MockComponent:
    """Represents the service requesting a history replay.
    
    When invoked will request history replay from exchange
    provided in config. Expects that History and EventStore are 
    running in testing mode and available.
    """

    def __init__(self, expected_msg_count):
        self.expected_msg_count = expected_msg_count
        self.config = Config()
        self.inbox = []

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

        # declare exchange
        self.channel.exchange_declare(
            exchange='history',
            exchange_type='direct'
        )

        # declare queues
        result = self.channel.queue_declare('', exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.queue_bind(
            exchange='history',
            queue=self.callback_queue
        )

    def send_msg(self, msg):
        self.channel.basic_publish(
            exchange='history',
            routing_key=self.config.RECV_QUEUE,
            body=msg,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                # don't need correlation id?
            )
        )

    def run(self):
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._recv
        )
        while len(self.inbox) < self.expected_msg_count:
            self.conn.process_data_events()

        # add an extra check for any further unexpected messages?  
        self.shutdown()  

    def _recv(self, ch, method_frame, properties, body):
        self.inbox.append(body)
        ch.basic_ack(delivery_tag=method_frame.delivery_tag)
        
        # gotta find a way to wait for message acknowledgement from send


    def shutdown(self):
        self.conn.close()


def test_replay_history(test_name: str, expected_msg_count: int, msg_start: int, priority_order: bool) -> None :
    """
    Currently relies on the existence of a dev database with a known quantity
    of events. Requests a replay and then returns the results.

    i could potentially open up a sqlalchemy session here and access the db directly
    """
    spacer = '\n\n'
    print('_' * 79 + spacer)
    print(f'Starting test {test_name}')

    producer = MockComponent(expected_msg_count=expected_msg_count)
    msg = json.dumps({
        "PRIORITY_SORT": priority_order,
        "LAST_EVENT_ID": msg_start
    })

    producer.send_msg(msg)
    producer.run()
    print(f'finished test. Got {len(producer.inbox)} messages:')
    for msg in producer.inbox:
        print(f'\t {json.loads(msg.decode())}')
    print(spacer)


if __name__ == "__main__":

    test_replay_history(
        'Get all messages in chronological order',
        expected_msg_count=3,
        msg_start=0,
        priority_order=False
    )

    test_replay_history(
        'Get all messages in priority order',
        expected_msg_count=3,
        msg_start=0,
        priority_order=True
    )

    test_replay_history(
        'Start after 1 in chronological order',
        expected_msg_count=2,
        msg_start=1,
        priority_order=False
    )

    test_replay_history(
        'Start after 1 in priority order',
        expected_msg_count=2,
        msg_start=1,
        priority_order=True
    )
