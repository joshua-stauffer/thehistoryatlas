"""Module to obtain data from geonames.org and return it in a form useable by 
the database.

This should be the only application code tightly coupled with the geonames
data source, and if other data sources are added down the road, they should
more or less present a consistent api.

May 21st, 2021"""

import asyncio
from collections import namedtuple
import logging
from os import stat
from zipfile import ZipFile
import requests
from app.errors import TooManyRetriesError

log = logging.getLogger(__name__)

CityRow = namedtuple('Row', [
    'geoname_id',
    'name',
    'ascii_name',
    'alternate_names',
    'latitude',
    'longitude',
    'modification_date' # yyyy-mm-dd
])

class GeoNames:
    """Class to encapsulate the process of fetching, cleaning, and presenting
    geo data obtained from geonames.org."""
    
    def __init__(self,
        resource_url: str
    ) -> None:
        self._resource_url = resource_url
        self._basedir = '/app/data/'
        self.RETRIES_ALLOWED = 3
        self.RETRY_TIMEOUT = 0.5

    def build(self):
        """Fetch and clean up data from resource_uri. Note that this is a
        blocking call that involves making network requests."""
        url, data = self._download_data(self._resource_url)
        zip_filename = self._write_zipfile(url, data)
        text_filename = self._extract_txt_from_zip(zip_filename)
        self.data = self._get_data(text_filename)
        return self.data

    def _download_data(self, uri):
        """Fetch a resource and return it as binary data"""
        # TODO: build this out and connect it.
        # for now, just reading this from a local file
        response = requests.get(uri)
        if response.status_code == requests.codes.ok:
            return uri, response.content

    def _write_zipfile(self, url: str, data: bin,) -> str:
        """Writes binary to a zipfile on disk and returns the filename"""
        # the last segment of the url is the resource name
        filename = self._basedir + url.split('/')[-1]
        print(f'Writing file {filename} to disk.')
        with open(filename, 'wb') as f:
            f.write(data)
        return filename

    @staticmethod
    def _extract_txt_from_zip(filename: str):
        """Writes the content of a zip file located at filename to the same
        location and returns a list of unzipped resource filenames"""
        print(f'Extracting text from filename {filename}')
        with ZipFile(filename) as z:
            # these zip files should all just have one txt file
            filename = z.extract(z.namelist()[0], path='./data')
        return filename

    @staticmethod
    def _get_data(path):
        """Opens a tsv text file and returns it as a list of lists"""
        r = list()
        print(f'Getting data from path {path}')
        with open(path, 'r') as f:
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
                r.append(row)
        return r
