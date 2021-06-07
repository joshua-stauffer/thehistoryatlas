import json
import os
import requests

cwd = os.getcwd()
fake_data_dir = cwd + '/builder/data/fake'
real_data_dir = cwd + '/builder/data/real'

API_URL = 'http://localhost:4000/'
src_dir = input(f"""

Welcome to the MockClient utility script!
This script will load any json files in a given source directory, and publish
their data to the graphql server running at {API_URL}.

To fill the database with around ~200,000 fake events, use:
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


for entry in data:
    # for testing purposes, delete summary
    del entry['summary']
    body = {
        'query': mutation,
        'variables': {'input': entry}
    }
    print('Posting ', entry)
    r = requests.post(API_URL, headers=headers, json=body)
    print(r.ok)
    print(r.text)
