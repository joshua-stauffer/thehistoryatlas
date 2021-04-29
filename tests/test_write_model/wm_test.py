
import asyncio
import json
import logging

from tackle import Tackle

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)

t = Tackle('any.txt')

input = json.loads('{"type": "PUBLISH_NEW_CITATION", "user": "joshki", "timestamp": "definitely right now", "payload": {"text": "oh hi there, some very interesting! sample! text!", "GUID": "fake-citation-3599", "tags": [], "meta": {}}}')
output = json.loads('{"type": "CITATION_PUBLISHED", "user": "joshki", "timestamp": "definitely right now", "priority": 1, "payload": {"text": "oh hi there, some very interesting! sample! text!", "GUID": "fake-citation-3599", "tags": [], "meta": {}}}')
data = [{
    'in': input,
    'out': output
}]

t.create_test(
    test_name='Test setup',
    input_routing_key='command.writemodel',
    output_routing_key='event.emitted',
    dataset=data
)

t.run_tests()
results = t.results()
