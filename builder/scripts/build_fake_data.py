"""
names generated with listofrandomnames.com
places generated from geonames.org
text generated from loremipsum.io
"""

from collections import defaultdict
from collections import deque
import json
import os
from pathlib import Path
import random
import string
import datetime
from uuid import uuid4

cwd = os.getcwd()

OUT_DIR = cwd + '/builder/data/fake/'
OUT_FILENAME = OUT_DIR + 'generated_events.json'
REPORT_FILENAME = OUT_DIR + 'generated_events_summary.txt'
RANDOM_SEED = 'the history atlas of the future'
MIN_YEAR = 2915
MAX_YEAR = 3315
MIN_LONGEVITY = 19
MAX_LONGEVITY = 102
MIN_EVENTS = 1
MAX_EVENTS = 500

# date constants
# randomly generated numbers less than this will result in a date of that specificity.
YEAR_THRESHOLD = 0.25
SEASON_THRESHOLD = 0.5
MONTH_THRESHOLD= 0.75
DAY_THRESHOLD = 1       # this falls through in an else clause anyways

# chance of an event having multiple people or places in an event
PERSON_1_THRESHOLD = 0.5
PERSON_2_THRESHOLD = 0.85
PERSON_3_THRESHOLD = 1
PLACE_1_THRESHOLD = 0.85
PLACE_2_THRESHOLD = 1
TIME_1_THRESHOLD = 0.85

DATA_SRC_DIR = cwd + '/builder/src_data/'
PEOPLE_PATH = DATA_SRC_DIR + 'people.txt'
PLACES_PATH = DATA_SRC_DIR + 'cities.json'
WORDS_PATH = DATA_SRC_DIR + 'words.txt'

MAX_LOOPS = 1000

random.seed(a=RANDOM_SEED)

# global map of entity: guid
entity_map = dict()

class Person:
    def __init__(self, name):
        """A fake person"""
        self.name = name
        self.event_count = random.randint(MIN_EVENTS, MAX_EVENTS)
        self.longevity = random.randint(MIN_LONGEVITY, MAX_LONGEVITY)
        self.birth_year = random.randint(MIN_YEAR, MAX_YEAR-self.longevity)
        self.death_year = self.birth_year + self.longevity

    def __repr__(self):
        return f'{self.name}, b. {self.birth_year}, d. {self.death_year}, {self.event_count} known events.'

def build():
    """The primary function of this script. Constructs the data and writes it to the output directory."""

    people = load_people()
    places = load_places()
    texts = load_texts()

    # add each person for each event instance they need
    people_by_event = deque()
    for person in people:
        for _ in range(person.event_count):
            people_by_event.append(person)
    random.shuffle(people_by_event)

    events = list()
    while len(people_by_event):
        # one event should be created each iteration
        person_count = get_num_people()
        if person_count > len(people_by_event):
            person_count = len(people_by_event)
        place_count = get_num_places()
        time_count = get_num_times()

        # get people, places, and times
        cur_people, start_date, end_date = get_people(
            people_by_event=people_by_event,
            person_count=person_count)
        cur_times = [generate_time(start=start_date, end=end_date)
                     for _ in range(time_count)]
        cur_places = random.sample(places, place_count)
        text = texts[random.randint(0, len(texts)-1)]
        entities = [*cur_people, *cur_places, *cur_times]
        citation = generate_citation(
            entities=entities,
            text=text)
        summary = generate_summary(
            entities=entities,
            text=text)
        tags = [generate_tag(entity, citation) for entity in entities]
        meta = generate_meta()
        events.append({
            'text': citation,
            'summary': summary,
            'tags': tags,
            'meta': meta
        })
    
    # write the resulting events to file

    with open(OUT_FILENAME, 'w') as f:
        json.dump(events, f)

    # calculate stats on generated data
    total_counter = defaultdict(set)
    for event in events:
        tags = event.get('tags')
        for tag in tags:
            total_counter[tag['type']].add(tag['guid'])
    totals = dict()
    totals['Event Count'] = len(events)
    totals['People Count'] = len(total_counter.get('PERSON'))
    totals['Places Count'] = len(total_counter.get('PLACE'))
    totals['Times Count'] = len(total_counter.get('TIME'))
    print('_' * 79)
    print('Generated new events file. Totals:')
    print(f'Events: {totals.get("Event Count"):>30}')
    print(f'People: {totals.get("People Count"):>30}')
    print(f'Places: {totals.get("Places Count"):>30}')
    print(f'Times:  {totals.get("Times Count"):>30}')
    print('_' * 79)
    write_report(totals)

# functions to create or obtain things

def generate_time(start: int, end: int) -> str:
    """Generates a random, valid date within the given range, in the format 
    expected by the History Atlas."""

    chance = random.random()
    year = random.randint(start, end)
    season = random.randint(1, 4)
    month = season * random.randint(1, 3)
    day = random.randint(1, 30) # happily running with a uniform 30 day month!
    if chance <= YEAR_THRESHOLD:
        return f'{year}'
    elif chance <= SEASON_THRESHOLD:
        return f'{year}|{season}'
    elif chance <= MONTH_THRESHOLD:
        return f'{year}|{season}|{month}'
    else:
        return f'{year}|{season}|{month}|{day}'

def generate_citation(entities: list, text: str) -> str:
    """Creates a fake citation with entity names embedded."""

    entity_names = get_names_from_entities(entities)
    tmp_text = text.split(' ')
    for entity in entity_names:
        tmp_text.insert(random.randint(0, len(tmp_text)), entity)
    return ' '.join(tmp_text)

def generate_summary(entities: list, text: str) -> str:
    """Creates a fake summary with entity names embedded"""

    entity_names = get_names_from_entities(entities)
    extra_word_count = random.randint(1, 10)
    tmp_text = random.sample(text, extra_word_count)
    for name in entity_names:
        tmp_text.insert(random.randint(0, len(tmp_text)), name)
    return ' '.join(tmp_text)  

def generate_tag(entity, text: str) -> dict:
    """Creates a tag instance based on an entity's location in the text."""

    tag = dict()
    if isinstance(entity, Person):
        type = 'PERSON'
        name = entity.name
    elif isinstance(entity, dict):
        type = 'PLACE'
        name = entity.get('name')
        latitude = entity.get('latitude')
        longitude = entity.get('longitude')
        tag['latitude'] = latitude
        tag['longitude'] = longitude
        tag['geoshape'] = None
    else:
        type = 'TIME'
        name = entity
    start_char = text.find(name)
    if start_char == -1:
        raise Exception(f'Entity {name} wasn\'t found in text {text}')
    stop_char = start_char + len(name)
    tag['name'] = name
    tag['type'] = type
    tag['start_char'] = start_char
    tag['stop_char'] = stop_char
    tag['guid'] = get_guid(name)
    return tag

def generate_meta() -> dict:
    """Returns a meta data dict with fields of random characters"""

    meta = dict()
    meta['author'] = ' '.join(get_random_string() for _ in range(2))
    meta['publisher'] = get_random_string()
    meta['title'] = ' '.join(get_random_string() for _ in range(random.randint(1, 5)))
    meta['guid'] = str(uuid4())
    return meta

def get_random_string(capitalize=False) -> str:
    """Returns a random 'word' of ascii letters."""

    length = random.randint(1, 10)
    word = [random.choice(string.ascii_lowercase) for _ in range(length)]
    if capitalize:
        word[0] = word[0].upper()
    return ''.join(word)

def get_num_people() -> int:
    chance = random.random()
    if chance <= PERSON_1_THRESHOLD:
        return 1
    elif chance <= PERSON_2_THRESHOLD:
        return 2
    else:
        return 3

def get_num_places() -> int:
    chance = random.random()
    if chance <= PLACE_1_THRESHOLD:
        return 1
    else:
        return 2

def get_num_times() -> int:
    chance = random.random()
    if chance <= TIME_1_THRESHOLD:
        return 1
    else:
        return 2

def get_guid(name: str) -> str:
    guid = entity_map.get(name)
    if not guid:
        guid = str(uuid4())
        entity_map[name] = guid
    return guid

def get_people(
    people_by_event: deque,
    person_count: int
    ) -> tuple[list, int, int]:
    """Tries to obtain person_count people from people_by_event, ensuring that
    their dates overlap. May return a list of less people than person_count."""
    if person_count > 1:
        cur_people = [people_by_event.popleft() for _ in range(person_count)]
        base_person = cur_people.pop()
        verified_people = [base_person]
        start_year = base_person.birth_year
        end_year = base_person.death_year
        while len(cur_people):
            cur_person = cur_people.pop()
            # no duplicate people
            if cur_person in verified_people:
                people_by_event.append(cur_person)
            # people must overlap times
            elif cur_person.birth_year > end_year or cur_person.death_year < start_year:
                people_by_event.append(cur_person)
            # otherwise, we have an overlap, so add person and narrow our window of time
            else:
                start_year = max(start_year, cur_person.birth_year)
                end_year = min(end_year, cur_person.death_year)
                verified_people.append(cur_person)
    else:
        cur_person = people_by_event.popleft()
        verified_people = [cur_person]
        start_year = cur_person.birth_year
        end_year = cur_person.death_year
    return verified_people, start_year, end_year

def get_names_from_entities(entities: list) -> list:
    entity_names = list()
    for entity in entities:
        if isinstance(entity, Person):
            entity_names.append(entity.name)
        elif isinstance(entity, dict):
            entity_names.append(entity['name'])
        else:
            entity_names.append(entity)
    return entity_names

# file utilities

def load_people():
    people = list()
    with open(PEOPLE_PATH, 'r') as f:
        for name in f.readlines():
            people.append(Person(name.strip()))
    return people

def load_places():
    with open(PLACES_PATH, 'r') as f:
        places = json.load(f)
    return places

def load_texts():
    texts = list()
    with open(WORDS_PATH, 'r') as f:
        for line in f.readlines():
            if len(line.strip()):
                texts.append(line.strip())
    return texts

def write_report(report: dict) -> None:

    with open(REPORT_FILENAME, 'w') as f:
        f.write('The History Atlas\n\n')
        f.write(f'Summary of mock data generated on {datetime.datetime.utcnow()}\n\n')
        f.write('_' * 79)
        f.write('\n')
        for k, v in report.items():
            f.write(f'{k:>35}:{v:>44}\n')
        f.write('_' * 79)


if __name__ == '__main__':
    build()