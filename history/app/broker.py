"""
RabbitMQ integration layer for the History Atlas History Player service.
"""
import pika

class Broker:

    def __init__(self, config, recv_func):
            self.EXCHANGE_NAME = 'history'
            self.reply_to = None
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

            # declare exchange
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_NAME,
                exchange_type='direct'
            )

            # declare and bind queue
            self.recv_queue = self.channel.queue_declare(
                queue=config.RECV_QUEUE,
                durable=True,
                auto_delete=False
            )
            self.channel.queue_bind(
                exchange=self.EXCHANGE_NAME,
                queue=self.config.RECV_QUEUE
            )

    def publish(self, msg):
        """Publishes param msg to the requested queue"""
        
        self.channel.basic_publish(
            exchange=self.EXCHANGE_NAME,
            routing_key=self.reply_to,
            body=msg
        )

    def listen(self):
        self.channel.basic_consume(
            self.config.RECV_QUEUE,
            on_message_callback=self.on_message    
        )
        try:
            print('History Player is ready for messages')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            raise KeyboardInterrupt()
        finally:
            self.connection.close()

    def on_message(self, channel, method_frame, header_frame, body):
        """Handles incoming messages and directs playback stream to
        the requesting client."""
        # transform message
        try:
            self.reply_to = header_frame.reply_to
            self.recv_func(body, self.publish)
            # acknowledge that this message has been handled
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            self.reply_to = None
    
        except ValueError:

            channel.basic_nack(
                requeue=False # uh.. not sure for this case
            )
            return
