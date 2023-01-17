from dataclasses import asdict

import pytest

from seed.commands import ADD_PEOPLE


@pytest.mark.asyncio
async def test_add_person(broker):
    await broker.connect(retry=True, retry_timeout=0.1, max_attempts=20)

    add_person_command = ADD_PEOPLE[0]

    msg = broker.create_message(body=asdict(add_person_command))
    result = await broker.publish_one(message=msg, routing_key="command.emitted")
    await broker.cancel()
