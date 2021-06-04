"""This script downloads data and parses from geonames.org, then
saves it to a file for use by the History Atlas's fake data generator.
"""

from collections import namedtuple
import json
import os
from zipfile import ZipFile
import requests


GEONAMES_URL = 'https://download.geonames.org/export/dump/cities15000.zip'
SRC_DATA_DIR = input('\n\nPlease enter the full path of the output directory:\n')
if not os.path.isdir(SRC_DATA_DIR):
    raise Exception(f'Provided path {SRC_DATA_DIR} is not a directory.')
OUT_FILENAME = SRC_DATA_DIR + 'cities.json'
cities = list()
Coordinates = namedtuple('Coordinates', ['longitude', 'latitude'])

upper_left_coord = Coordinates(
    # La Concepción, Chiriquí
    longitude = -82.7,
    latitude = 8.6)
lower_right_coord = Coordinates(
    # King Edward Point
    longitude = -54.3,
    latitude = -36.5)

def is_in_box(longitude: float, latitude: float) -> bool:
    """utility function to check if coordinates are inside the box defined 
    by upper_left_coord and lower_right_coord."""
    if longitude > upper_left_coord.longitude \
        and longitude < lower_right_coord.longitude \
        and latitude < upper_left_coord.latitude \
        and latitude > lower_right_coord.latitude:
        return True
    else:
        return False

CityRow = namedtuple('Row', [
    'geoname_id',
    'name',
    'ascii_name',
    'alternate_names',
    'latitude',
    'longitude',
    'modification_date' # yyyy-mm-dd
])

# get the data from geonames.org
response = requests.get(GEONAMES_URL)
if not response.status_code == requests.codes.ok:
    print(response.json)
    raise Exception('Unable to get Geonames data because an exception occurred.')

# write the data to a zip file
zipfile_name = SRC_DATA_DIR + 'geonames.zip'
with open(zipfile_name, 'wb') as f:
    f.write(response.content)

# extract the zip file to text file
with ZipFile(zipfile_name) as z:
    # these zip files should all just have one txt file
    textfile_name = z.extract(z.namelist()[0], path=SRC_DATA_DIR)

# read and parse the text file
with open(textfile_name, 'r') as f:
    for line in f.readlines():
        tmp_row = line.split('\t')
        row = CityRow(
            geoname_id        = int(tmp_row[0]),
            name              = tmp_row[1],
            ascii_name        = tmp_row[2],
            alternate_names   = tmp_row[3],
            latitude          = float(tmp_row[4]),
            longitude         = float(tmp_row[5]),
            modification_date = tmp_row[18])
        if is_in_box(
            longitude=row.longitude,
            latitude=row.latitude):
            cities.append({
                'geoname_id': row.geoname_id,
                'name': row.name,
                'ascii_name': row.ascii_name,
                'alternate_names': row.alternate_names,
                'latitude': row.latitude,
                'longitude': row.longitude,
                'modification_date': row.modification_date
            })

with open(OUT_FILENAME, 'w') as f:
    json.dump(cities, f)
print(f'Finished processing {len(cities)} places.')
