from unittest.mock import AsyncMock

import pytest

from rpc_manager import RPCManager, RPCSuccess, RPCFailure


@pytest.mark.asyncio
async def test_manager_calls_remote():

    pub_func = AsyncMock()
    manager = RPCManager(timeout=0, pub_function=pub_func)
    message = {"type": "test-message"}
    await manager.make_call(message=message)

    pub_func.assert_called_once()


@pytest.mark.asyncio
async def test_manager_returns_success():
    SEND_MESSAGE = {"type": "test-message"}
    RECEIVE_MESSAGE = {"type": "success!"}
    TIMEOUT = 0.001  # any faster and the test fails
    update_func_closure = []

    async def pub_func(message, corr_id):
        nonlocal update_func_closure
        update_func_closure[0](corr_id)

    manager = RPCManager(timeout=TIMEOUT, pub_function=pub_func)

    def _update_func(corr_id):
        nonlocal manager
        manager._result_store[corr_id] = RECEIVE_MESSAGE

    update_func_closure.append(_update_func)

    result = await manager.make_call(message=SEND_MESSAGE)
    assert result == RPCSuccess(message=RECEIVE_MESSAGE)


@pytest.mark.asyncio
async def test_manager_returns_failure():

    pub_func = AsyncMock()
    manager = RPCManager(timeout=0, pub_function=pub_func)
    message = {"type": "test-message"}
    result = await manager.make_call(message=message)
    assert result == RPCFailure()
