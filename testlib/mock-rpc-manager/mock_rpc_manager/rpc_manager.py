from collections import deque
from typing import Callable, Awaitable, Dict, Union, List

from rpc_manager import RPCResponse, RPCFailure, RPCManager


class MockRPCManager(RPCManager):
    def __init__(
        self,
        timeout: Union[int, float],
        pub_function: Callable[[Dict, str], Awaitable[None]],
    ):
        super().__init__(timeout=timeout, pub_function=pub_function)
        self._queue = deque()
        self.messages = []

    def add_response(self, response: RPCResponse) -> None:
        """
        Load the RPCResponse object to be returned by make_call.
        """
        self._queue.append(response)

    def add_responses(self, responses: List[RPCResponse]) -> None:
        """
        Load an ordered list of RPCResponse objects to be returned by make_call.
        """
        for response in responses:
            self._queue.append(response)

    async def make_call(self, message: Dict) -> RPCResponse:
        self.messages.append(message)
        try:
            return self._queue.popleft()
        except IndexError:
            # default behavior
            return RPCFailure()

    def handle_response(self, message: dict, corr_id: str) -> None:
        raise NotImplementedError
