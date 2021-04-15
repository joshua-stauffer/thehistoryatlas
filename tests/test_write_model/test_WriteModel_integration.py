"""
This integration test sets up mock components to integrate with the WriteModel.
Results are printed to the terminal:
    Command Entered
    Event Returned
"""

import os
import json
import pika
import pytest

class MockProducer:

    def __init__(self):
        self.host = os.environ.get('HOST_NAME') or 'localhost'
        self.conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        self.channel = self.conn.channel()
        self.channel.queue_declare(
            'commands',
            durable=True,
            auto_delete=False
        )

    def send_msg(self, msg):
        self.channel.basic_publish(
            exchange='',
            routing_key='commands',
            body=msg
        )
        
    def shutdown(self):
        self.conn.close()

class MockConsumer:

    def __init__(self):
        self.host = os.environ.get('HOST_NAME')
        self.conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        self.channel = self.conn.channel()
        self.channel.queue_declare(
            'emitted_events',
            durable=True,
            auto_delete=False
        )
        self.inbox = None

    def get_msgs(self):
        self.channel.basic_consume(
            'emitted_events',
            self._recv
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

def test_add_person():
    # requires that the WriteModel is up and running
    producer = MockProducer()
    consumer = MockConsumer()
    msg = json.dumps({
        'type': 'AddPerson',
        'timestamp': 'now!',
        'user': 'test_user',
        'payload': {
            'name': 'frederick the great'
        }
    })
    result = {
        'type': 'PersonAdded',
        'timestamp': 'now!',
        'user': 'test_user',
        'payload': {
            'name': 'frederick the great'
        }
    }
    producer.send_msg(msg)
    consumer.get_msgs()

    assert json.loads(consumer.inbox.decode()) == result
    print('this function ran!')
