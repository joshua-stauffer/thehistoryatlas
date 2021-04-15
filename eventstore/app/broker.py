"""
RabbitMQ integration layer for the History Atlas Event Store service.
"""
import pika

class Broker:

    def __init__(self, config, recv_func):
        self.config = config
        self.recv_func = recv_func

        # get connection and channel
        credentials = pika.PlainCredentials(
            self.config.BROKER_USERNAME,
            self.config.BROKER_PASS
        )
        conn_params = pika.ConnectionParameters(
            host=self.config.NETWORK_HOST_NAME,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(conn_params)
        self.channel = self.connection.channel()

        # declare exchanges
        self.channel.exchange_declare(
            exchange='emitted_events',
            exchange_type='direct'
        )
        self.channel.exchange_declare(
            exchange='persisted_events',
            exchange_type='fanout'
        )

        # declare and bind queues
        self.recv_queue = self.channel.queue_declare(
            queue=config.RECV_QUEUE,
            durable=True,
            auto_delete=False
        )
        self.channel.queue_bind(
            exchange='emitted_events',
            queue=self.config.RECV_QUEUE
        )
        self.send_queue = self.channel.queue_declare(
            queue=self.config.SEND_QUEUE,
            durable=True,
            auto_delete=False
        )
        self.channel.queue_bind(
            exchange='persisted_events',
            queue=self.config.SEND_QUEUE
        )

    def publish(self, msg):
        """Publishes param msg to the persisted_events fanout exchange"""
        
        self.channel.basic_publish(
            exchange='persisted_events',
            routing_key='',     # fanout exchanges don't use a routing key
            body=msg
        )

    def listen(self):
        self.channel.basic_consume(
            self.config.RECV_QUEUE,
            on_message_callback=self.on_message    
        )
        try:
            print('EventStore is ready for messages')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            raise KeyboardInterrupt()
        finally:
            self.connection.close()

    def on_message(self, channel, method_frame, header_frame, body):
        # transform message
        try:
            msg = self.recv_func(body)
            # acknowledge that this message has been handled
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    
        except ValueError:      # this needs to reflect the exception that 
                                # the database will throw on failure

            channel.basic_nack(
                requeue=True    # we should try again
            )
            return              # but we'll return first so that the event isn't published 

        # publish the persisted event
        self.publish(msg)
