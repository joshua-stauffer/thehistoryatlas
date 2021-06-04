"""
names generated with listofrandomnames.com
places generated from geonames.org
text generated from loremipsum.io
"""
from collections import deque
import json
import random
import os

# OUT_DIR = input('\n\nPlease enter the complete path of the output directory:\n')
# if not os.path.isdir(OUT_DIR):
#    raise Exception(f'Provided path {OUT_DIR} is not a directory.')
OUT_DIR = '/Users/jds/dev/history-atlas/builder/data/fake/'
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

# DATA_SRC_DIR = input('\n\nPlease enter the complete path of the data source directory:\nDirectory should contain:\n\tpeople.txt\n\tcities.json\n\twords.txt')
# if not os.path.isdir(DATA_SRC_DIR):
#    raise Exception(f'Provided path {DATA_SRC_DIR} is not a directory.')
DATA_SRC_DIR = '/Users/jds/dev/history-atlas/builder/src_data/'
PEOPLE_PATH = DATA_SRC_DIR + 'people.txt'
PLACES_PATH = DATA_SRC_DIR + 'cities.json'
WORDS_PATH = DATA_SRC_DIR + 'words.txt'

MAX_LOOPS = 1000

random.seed(a=RANDOM_SEED)

# people
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


def generate_citation(people, places, times):
    ...

def get_num_people():
    chance = random.random()
    if chance <= PERSON_1_THRESHOLD:
        return 1
    elif chance <= PERSON_2_THRESHOLD:
        return 2
    else:
        return 3

def get_num_places():
    chance = random.random()
    if chance <= PLACE_1_THRESHOLD:
        return 1
    else:
        return 2

def get_num_times():
    chance = random.random()
    if chance <= TIME_1_THRESHOLD:
        return 1
    else:
        return 2


def build():
    """The primary function of this script. Constructs the data and writes it to the output directory."""
    # get people
    people = list()
    with open(PEOPLE_PATH, 'r') as f:
        for name in f.readlines():
            people.append(Person(name.strip()))
    # get places
    with open(PLACES_PATH, 'r') as f:
        places = json.load(f)
    
    # get texts
    texts = list()
    with open(WORDS_PATH, 'r') as f:
        for line in f.readlines():
            if len(line.strip()):
                texts.append(line.strip())

    # add each person for each event instance they need
    people_by_event = deque()
    for person in people:
        for _ in range(person.event_count):
            people_by_event.append(person)
    random.shuffle(people_by_event)

    print(f'there are {len(people_by_event)} events')

    citations = list()
    while len(people_by_event):
        # one event should be created each iteration
        person_count = get_num_people()
        if person_count > len(people_by_event):
            person_count = len(people_by_event)
        place_count = get_num_places()
        time_count = get_num_times()

        # get people, ensuring overlap in times
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
        
    print('done!')

    #    cur_places = random.sample(places, place_count)








if __name__ == '__main__':
    build()