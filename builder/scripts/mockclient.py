import json
import os
import datetime
import time
import requests

POSTS_PER_SECOND = 1000

cwd = os.getcwd()
fake_data_dir = cwd + '/builder/data/fake'
real_data_dir = cwd + '/builder/data/real'

API_URL = 'http://localhost:4000/'
src_dir = input(f"""

Welcome to the MockClient utility script!
This script will load any json files in a given source directory, and publish
their data to the graphql server running at {API_URL}.

To fill the database with around script-generated fake events, use:
    {fake_data_dir}

To fill the database with a (limited) amount of real data, use:
    {real_data_dir}

Please enter the full path of your source directory:
""")

data = list()

for file in os.scandir(src_dir):
    if os.path.isfile(file) and file.name.endswith('.json'):
        with open(file.path, 'r') as f:
            json_file = json.load(f)
            for entry in json_file:
                data.append(entry)

mutation = """
mutation publishWithVariables($input: AnnotateCitationInput!) {
  PublishNewCitation(AnnotatedCitation: $input) {
    code
    success
    message
  }
}
"""

headers = {
    'Content-Type': 'application/json',
    'Origin': 'http://localhost:4000',
    'Accept': 'application/json',
    'DNT': '1'
}

total = len(data)
block = total // 79 # console width

start = datetime.datetime.utcnow()
next_start = start + datetime.timedelta(seconds=1)
for i, entry in enumerate(data):
    # print status bar
    if i % block == 0:
        progress_count = i // block
        print('.' * progress_count)

    # limit amount published per second
    """ 
    if (i + 1) % POSTS_PER_SECOND == 0:
        now = datetime.datetime.utcnow()
        if now < next_start:
            timedelta = next_start - now
            ms = timedelta.microseconds
            seconds = ms / 1000000
            print(f'Sent {POSTS_PER_SECOND} in {1 - seconds} seconds. Now sleeping for {seconds} seconds')
            time.sleep(seconds)
        else:
            print('Publishing time exceeded one second.')
            next_start = now + datetime.timedelta(seconds=1)
    """

    # for testing purposes, delete summary
    del entry['summary']
    body = {
        'query': mutation,
        'variables': {'input': entry}
    }
    r = requests.post(API_URL, headers=headers, json=body)
    if not r.ok:
        print('Request failed: ', r.json())
print(f'Finished publishing {len(data)} events in {datetime.datetime.utcnow()-start}.')