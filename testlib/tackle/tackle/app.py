import asyncio
from collections import deque
from collections.abc import Callable
import datetime
import json
import logging
from uuid import uuid4
from typing import Union
from .test_broker import Broker
from .types import DataSet

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class Tackle:
    """A test harness framework for automating integration testing within a
    system communicating via AMQP. Designed to answer the questions:

        "What's coming in? and what is going out? and how fast can
        those two things happen? And when do things begin to break
        down?"
    """

    def __init__(self, output_path):
        self.output_filename = output_path
        self._tests = deque()
        self._results = dict()

    def create_test(
        self,
        test_name: str,
        input_routing_key: str,
        output_routing_key: str,
        dataset: DataSet,
        runs: int = 1,
        test_timeout: Union[int, float] = 3,
    ) -> None:
        """A hook which registers a single test.

        Sends all messages, waits for test_timeout, then checks the results.
        """
        test_results = dict()

        def process_response(message):
            """A callback passed to the broker which will process all incoming
            messages on a given routing key."""

            corr_id = message.headers["corr_id"]
            body_bytes = message.body
            body = json.loads(body_bytes.decode())
            test_results[corr_id]["end_time"] = str(datetime.datetime.utcnow())
            if test_results[corr_id] == body:
                test_results[corr_id]["result"] = True
                return True
            test_results[corr_id]["result"] = False
            return False

        async def test():
            """The actual test unit."""
            log.info(f"Starting test {test_name}")
            broker = Broker()
            await broker.connect(retry=True, retry_timeout=0.1)
            pub = broker.get_publisher(input_routing_key)
            await broker.add_message_handler(
                routing_key=output_routing_key, callback=process_response
            )
            for data in dataset:
                corr_id = str(uuid4())
                body = data["in"]
                msg = broker.create_message(body, headers={"corr_id": corr_id})
                start_time = str(datetime.datetime.utcnow())
                test_results[corr_id] = {
                    "start_time": start_time,
                    "end_time": None,
                    "in": data["in"],
                    "out": data["out"],
                    "result": None,
                }
                await pub(msg)
            await asyncio.sleep(test_timeout)
            await broker.cancel()

        # test.name = test_name # thought this was cool but probably not necessary
        self._tests.append(test)
        self._results[test_name] = test_results

    def run_tests(self):
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(t()) for t in self._tests]
        loop.run_until_complete(*tasks)

    def results(self):
        """Log all results."""
        # TODO: send these someplace more useful
        log.info("Tackle Results:")
        for k, v in self._results.items():
            log.info("_" * 79)
            log.info(k + " \n " + json.dumps(v))
            log.info("_" * 79)

    def load_data(self, path):
        """Accepts a path to json file of data and imports it into application"""

        log.info(f"Loading data from {path}")
        with open(path, "r") as f:
            text = f.read()
        data = json.loads(text)
        log.debug("Loaded this json: " + json.dumps(data))
        return data
