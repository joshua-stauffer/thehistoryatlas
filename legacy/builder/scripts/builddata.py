"""
A functional script to quickly build testing data from the command line.
"""

import json
import os
from uuid import uuid4
from enum import Enum

class EntityType(Enum):
    PERSON = 'PERSON'
    PLACE = 'PLACE'
    TIME = 'TIME'

# global dict object for tracking guids
guidstore = dict()

def build():
    clear()
    print("""
    
    Welcome to the History Atlas's command line data building tool!

                        🌎        🌍        🌏  

    Each time you run this tool you will create a json file in an output
    folder of your choice. This tool is designed to input data from a 
    single source at a time -- it allows you to enter metadata at the
    start, and then assumes that the rest of the data you enter should
    be associated with that metadata.
    
    Let's start by getting your source metadata.
    """)
    meta = get_meta()
    path, out_dir = get_path()
    load_known_guids(out_dir)
    data = list()
    while user_input := create_entry(meta):
        clear()
        data.append(user_input)
    clear()
    print('Data entry finished: now saving to disk.')
    # write the data to disk
    with open(path, 'w') as f:
        json.dump(data, f)
    print('Data has been saved to ', path)
    print('Goodbye!')

def create_entry(meta):
    """Supervises creating an entire GraphQL variable dict"""
    if not confirm(message='Create a new citation?'):
        return None
    text = enter_text()
    tags = enter_tags(text)
    summary = enter_summary(text, tags)
    return {
        'text': text,
        'summary': summary,
        'tags': tags,
        'meta': meta
    }

# tag utilities

def enter_tags(text: str) -> list:
    """Prompts the user to create a list of tags, and returns them"""
    tags = list()

    while confirm(message='Create a new tag?'):
        clear()
        print(text)
        tags.append(create_tag(text))
        print('Current tags:')
        for tag in tags:
            print(f"{tag.get('type'):<20} {tag.get('name')}")
    return tags

def create_tag(text: str) -> dict:
    """Entry point to making a tag. Discovers which tag should be created, and calls
    the appropriate function. 
    
    Returns a created tag.
    """
    while True:
        res = input("""
Please select an entity type: 
    1) PERSON
    2) PLACE
    3) TIME
        """)
        try:
            int_res = int(res)
            if int_res == 1:
                return create_person_tag(text)
            elif int_res == 2:
                return create_place_tag(text)
            elif int_res == 3:
                return create_time_tag(text)
            else:
                print(f"""
You entered {int_res}, which isn't a valid entry.
Please enter 1, 2, or 3.
                """)
        except ValueError:
            print('Please enter 1, 2, or 3')

def create_person_tag(text):
    """Input values to create a person tag"""

    name, start_char, stop_char = find_name(text)
    guid = get_guid(name)
    
    return make_tag(
        entity_type=EntityType.PERSON,
        name=name,
        start_char=start_char,
        stop_char=stop_char,
        GUID=guid)

def create_place_tag(text):
    """Input values to create a place tag"""

    name, start_char, stop_char = find_name(text)
    guid = get_guid(name)
    latitude, longitude = get_geo()

    return make_tag(
        entity_type=EntityType.PLACE,
        name=name,
        start_char=start_char,
        stop_char=stop_char,
        GUID=guid,
        latitude=latitude,
        longitude=longitude,
        geoshape=None)

def create_time_tag(text):
    """Input values to create a time tag"""

    name, start_char, stop_char = find_name(text)
    time_name = get_time_name()
    guid = get_guid(time_name)

    return make_tag(
        entity_type=EntityType.TIME,
        name=time_name,
        start_char=start_char,
        stop_char=stop_char,
        GUID=guid)

def find_name(text) -> tuple[str, int, int]:
    """Searches parameter text for a name given by the user, and calculates its indices."""

    while True:
        name = enter_name()
        start_char = text.find(name)
        stop_char = start_char + len(name)
        if start_char >= 0:
            msg = f'Is {text[start_char:stop_char]} the name you meant?'
            if not confirm(message=msg):
                # skip to the next iteration of the loop
                start_char = get_int(message='Please enter the index of the start character')
                stop_char = get_int(message='Please enter the index of the stop character')
            if confirm(message=f'Confirm {name} from {start_char} to {stop_char}?'):
                return name, start_char, stop_char
        else:
            msg = 'No entity by that name was found in the text. Are you tagging an entity not explicitly mentioned in this text?'
            if confirm(message=msg):
                start_char = 0
                stop_char = 0
                return name, start_char, stop_char
def make_tag(
    entity_type: EntityType,
    name: str,
    start_char: int,
    stop_char: int,
    GUID: str,
    latitude: float=None,
    longitude: float=None,
    geoshape: str=None
) -> dict:
    if entity_type == EntityType.PLACE:
        return {
            'type': 'PLACE',
            'name': name,
            'start_char': start_char,
            'stop_char': stop_char,
            'GUID': GUID,
            'latitude': latitude,
            'longitude': longitude,
            'geoshape': geoshape
        }

    elif entity_type == EntityType.PERSON:
        return {
            'type': 'PERSON',
            'name': name,
            'start_char': start_char,
            'stop_char': stop_char,
            'GUID': GUID
        }  
    elif entity_type == EntityType.TIME:
        return {
            'type': 'TIME',
            'name': name,
            'start_char': start_char,
            'stop_char': stop_char,
            'GUID': GUID
        }

    else:
        raise Exception(f'Unknown entity type {entity_type}')

# meta utilities

def get_meta() -> dict:
    while True:
        title = input('Please enter the title of your source\n')
        if confirm(val=title):
            break
    while True:
        author = input('Please enter the author/authors of your source\n')
        if confirm(val=author):
            break            
    while True:
        publisher = input('Please enter the publisher of your source\n')
        if confirm(val=publisher):
            break
    while True:
        if confirm(message="Do you have a GUID to enter for this source? This would be the case if you've entered data from this source before. Otherwise, we'll make one for you."):
            guid = input('Please enter the GUID: \n')
            if confirm(val=guid):
                break
        else:
            guid = str(uuid4())
            break
    return make_meta(
        title=title,
        author=author,
        publisher=publisher,
        GUID=guid)

def make_meta(
    title: str,
    author: str,
    publisher: str,
    GUID: str
) -> dict:
    return {
        'title': title,
        'author': author,
        'publisher': publisher,
        'GUID': GUID
    }

# summary utilities

def enter_summary(text, tags):
    clear()
    print(text)
    for tag in tags:
        print(f'\t{tag.get("type"):<20} {tag.get("name")}')
    summary = input('\nEnter a summary for this text -- it should be terse, and use each entity name. \n\tex: Biber was baptized on August 12th, 1644 in Wartenberg.\n')
    if confirm(val=summary):
        return summary
    else:
        return enter_summary(text, tags)

# path utilities

def join_path(root, filename):
    if root.endswith('/'):
        return root + filename
    else:
        return root + '/' + filename

# input functions

def confirm(val=None, message=None):
    """Prompt user to confirm something. Will prompt on val or message -- if val is
    provided, message is ignored. If neither are provided, an generic confirm 
    message will be used."""
    if val:
        msg = f'Confirm {val}?'
    elif message:
        msg = message 
    else:
        msg = 'Would you like to confirm your choice? '
    prompt = '\n' + msg + '\n✅ Press enter/return to confirm, or enter any key to cancel.\n'
    positive = ['']
    res = input(prompt)
    if res in positive:
        return True
    else:
        return False

def get_guid(name: str) -> str:
    """Obtains a GUID and keeps the GUID store up to date."""
    if guid := guidstore.get(name):
        if confirm(message=f'GUID found for that name. Use guid {guid}?'):
            return guid
    if not confirm(message='GUID not found. Enter any key to search for it under a different name.'):
        secondary_name = input('Enter the name: \n')
        if guid := guidstore.get(secondary_name):
            if confirm(message=f'Use guid {guid}?'):
                guidstore[name] = guid
                return guid
    if not confirm(message='Enter any key to see all known GUIDs'):
            for k, v in guidstore.items():
                print(f'{k:<30}{v}')
    while True:
        if confirm(message=f'Would you like to automatically create a new GUID for {name}?'):
            guid = str(uuid4())
            guidstore[name] = guid
            return guid
        guid = input('Enter the GUID you wish to use: \n')
        if confirm(val=guid):
            guidstore[name] = guid
            return guid

def get_geo():
    while True:
        long_str = input('Enter longitude: (E or W, and W should be a negative number) \n')
        try:
            longitude = float(long_str)
            if confirm(val=longitude):
                break
        except ValueError:
            print('That wasn\'t a floating point number.')
    while True:
        lat_str = input('Enter latitude: (N or S, and S should be a negative number) \n')
        try:
            latitude = float(lat_str)
            if confirm(val=latitude):
                break
        except ValueError:
            print('That wasn\'t a floating point number.')
    return longitude, latitude

def get_time_name() -> str:
    while True:
        year = input("Please enter the year as xxxx\n")
        if confirm(message='Would you like to enter a season (quarter)?'):
            return get_season(year)
        if confirm(val=year):
            return year

def get_season(year):
    valid_seasons = ['1', '2', '3', '4']
    while True:
        season = input("Please enter the season or quarter (1, 2, 3, or 4)\n")
        if season in valid_seasons:
            if confirm(val=season):
                date_str = year + '|' + season
                if confirm(message='Would you like to add a month?'):
                    return get_month(date_str)
                else:
                    return date_str
        else:
            print('That wasn\'t a valid season')

def get_month(date_str):
    valid_months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    while True:
        month = input("Please enter the month (number 1-12)\n")
        if month in valid_months:
            if confirm(val=month):
                date_str = date_str + '|' + month
                if confirm(message='Would you like to add a day?'):
                    return get_day(date_str)
                else:
                    return date_str
        else:
            print('That wasn\'t a valid month')

def get_day(date_str):
    valid_days = [str(n) for n in range(1, 32)]
    while True:
        day = input("Please enter the day (number 1-31)\n")
        if day in valid_days:
            if confirm(val=day):
                date_str = date_str + '|' + day
                return date_str
        else:
            print('That wasn\'t a valid day')

def enter_text():
    while True:
        text = input("\nEnter the text field:\n")
        if confirm(val=text):
            return text

def enter_name():
    while True:
        name = input("\nEnter the entity name as found in the text:\n")
        if confirm(val=name):
            return name

def get_int(message):
    while True:
        res = input(message + '\n')
        try:
            num = int(res)
            return num
        except ValueError:
            print('That wasn\'t a number.')

def get_path() -> tuple[str, str]:
    """Parent function for getting a valid output path from user"""
    while True:
        out_dir = get_dir_path()
        filename = get_filename()
        path = join_path(out_dir, filename)
        if os.path.exists(path):
            if confirm(message='That path exists -- if you continue, you will overwrite a file.'):
                return path, out_dir
        else:
            return path, out_dir

def get_dir_path():
    while True:
        path = input("\nPlease enter the directory you would like to use to store the data:\n")
        if os.path.isdir(path):
            if confirm(path):
                return path
        else:
            print(f'Sorry, the path you entered is not a directory.')

def get_filename():
    while True:
        name = input("\nPlease name your new file (without extension):\n")
        if confirm(name):
            return name + '.json'

def load_known_guids(path):
    print('Checking directory files for known GUIDs...')
    for file in os.scandir(path):
        if os.path.isfile(file) and file.name.endswith('.json'):
            with open(file.path, 'r') as f:
                json_file = json.load(f)
                for entry in json_file:
                    for tag in entry.get('tags'):
                        name = tag.get('name')
                        guid = tag.get('GUID')
                        if name and guid:
                            guidstore[name] = guid
    print(f'Found and added {len(guidstore.keys())} guids.')
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == '__main__':
    build()