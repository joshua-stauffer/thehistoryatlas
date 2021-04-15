"""
RabbitMQ integration layer for the History Atlas WriteModel service.
"""

import pika

class Broker:

    def __init__(self, config, recv_func):
        self.config = config
        self.recv_func = recv_func
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=config.NETWORK_HOST_NAME)
        )
        self.channel = self.connection.channel()
        self.recv_queue = self.channel.queue_declare(
            queue=self.config.RECV_QUEUE,
            durable=True,
            auto_delete=False
        )
        self.send_queue = self.channel.queue_declare(
            queue=self.config.SEND_QUEUE,
            durable=True,
            auto_delete=False
        )

    def listen(self):
        self.channel.basic_consume(
            self.config.RECV_QUEUE,
            on_message_callback=self._on_message    
        )
        try:
            print('WriteModel is ready for messages')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            raise KeyboardInterrupt()
        finally:
            self.connection.close()

    def _on_message(self, channel, method_frame, header_frame, body):
        # transform message
        try:
            # how can i filter out who the message is coming from?
            msg = self.recv_func(body)

            # acknowledge that this message has been handled
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    
        except ValueError:

            channel.basic_nack(
                requeue=False # invalid command
            )
            return

        # pass the message forward
        print('ready to publish message: ', msg)
        self.channel.basic_publish(
            '',
            self.config.SEND_QUEUE,
            msg
        )

    def replay_history(self):
        raise NotImplementedError()

    def shutdown(self):
        self.connection.close()