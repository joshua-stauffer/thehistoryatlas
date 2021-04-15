"""Entry point for the WriteModel component.

"""

import os
import json
from broker import Broker
from config import Config
from state_manager.manager import Manager


class WriteModel:

    def __init__(self):
        self.config = Config()
        self.manager = Manager(self.config)
        self.handle_command = self.manager.command_handler.handle_command
        self.handle_event = self.manager.event_handler.handle_event
        self.broker = None    # created in run_forever()

    def command_to_event(self, raw_msg: bin):
        """Passes incoming Command to the CommandHandler for processing and
        returns the result.
        
        params:
            raw_msg: binary repr of Command
            
        returns a json string
        """
        
        msg = raw_msg.decode()
        event = self.handle_command(msg)
        return json.dumps(event)

    def run_forever(self):

        while True:
            try:
                # get a new connection to RabbitMQ
                print('starting broker')
                self.broker = Broker(
                    self.config,
                    self.command_to_event,
                    # eventually need to handle events here too
                )
                self.broker.listen()
            except KeyboardInterrupt:
                print('shutting down the Write Model')
                return
            except Exception as e:
                print(f'Error in RabbitMQ connection ... {e}')
                self.broker.shutdown()
    

if __name__ == '__main__':
    wm = WriteModel()
    wm.run_forever()
