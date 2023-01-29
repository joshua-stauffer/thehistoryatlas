import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import getLogger
from typing import Dict, Callable, Union, Awaitable, Optional
from uuid import uuid4

log = getLogger(__name__)


@dataclass(frozen=True)
class RPCSuccess:
    message: Dict


@dataclass(frozen=True)
class RPCFailure:
    """Returned when no response is received from the remote call."""

    errors: Optional[Dict] = None


RPCResponse = Union[RPCSuccess, RPCFailure]


class RPCManager:
    """
    Component to execute asynchronous remote procedure calls.
    """

    def __init__(
        self,
        timeout: Union[int, float],
        pub_function: Callable[[Dict, str], Awaitable[None]],
    ):
        self._timeout = timeout
        self._pub_function = pub_function
        self._result_store: Dict[str, Optional[Dict]] = {}
        self._poll_offset = 0

    def handle_response(self, message: dict, corr_id: str) -> None:
        """
        Message handler to field incoming responses.
        """
        if corr_id not in self._result_store.keys():
            # no one's waiting for this message
            log.info("Received response too late.")
            return
        self._result_store[corr_id] = message

    async def make_call(self, message: Dict) -> RPCResponse:
        """Make a call to the remote source and wait for a response."""
        corr_id = str(uuid4())
        self._result_store[corr_id] = None
        start_time = datetime.utcnow()
        stop_time = start_time + timedelta(seconds=self._timeout)
        await self._pub_function(message, corr_id)

        # wait for a result
        while datetime.utcnow() < stop_time:
            await asyncio.sleep(self._poll_offset)
            if self._result_store[corr_id] is not None:
                response = self._result_store[corr_id]
                del self._result_store[corr_id]
                return RPCSuccess(message=response)

        return RPCFailure()

    def get_response_handler(self) -> Callable[[Dict, str], None]:
        return self.handle_response
