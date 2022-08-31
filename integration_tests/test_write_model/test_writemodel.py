
import asyncio
import json
import logging

import pytest

from tackle import Tackle
from seed import PUBLISH_CITATIONS, SYNTHETIC_EVENTS

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)

@pytest.mark.asyncio

async def test_writemodel():
    t = Tackle(output_path='any.txt')


    t.create_test(
        test_name='Test setup',
        input_routing_key='command.writemodel',
        output_routing_key='event.emitted',
        dataset=[{
            "input": PUBLISH_CITATIONS[0],
            "output": SYNTHETIC_EVENTS[0]
        }]
    )

    t.run_tests()
    results = t.results()
    print(results)
