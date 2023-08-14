# Builder
This component consists of a series of scripts used to generate and manage data in development.
- [builddata](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/builddata.py): a command-line tool to help quickly create annotations of real data sources (6.24.21: not updated for recent API changes)
- [build_geo_src](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/build_geo_src.py): sources geo data from geonames.org and saves it to disk for the use by other scripts.
- [build_fake_data](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/build_fake_data.py): a script to generate a large amount of fake (but realistically interconnected) related data.
- [mock_client](https://github.com/joshua-stauffer/thehistoryatlas/blob/dev/builder/scripts/mockclient.py): a tool to programmatically publish data from json files to the GraphQL API endpoint.

Base resources for generating fake data (names and ipsum lorem, and geo data, once the ```build_fake_data``` script has been run) can be found in the ```src_data``` directory.

The resulting application-ready data can be found in the ```data``` directory.

## Running the scripts
All scripts should be run from the root directory after activating the testing virtual environment with:
```shell
source test_env/bin/activate
```

Then, any of the scripts can be run with the following commands (still from the root directory):
 - builddata

```shell 
python builder/scripts/builddata.py
```

 - build_geo_src:
```shell
python builder/scripts/build_geo_src.py
```

 - build_fake_data:
```shell
python builder/scripts/build_fake_data.py
```

 - mockclient:
```shell
python builder/scripts/mockclient.py
```