import pytest
from app.geonames import GeoNames
from app.geonames import CityRow
from requests.exceptions import ConnectionError

def test_raises_error_with_invalid_uri():
    geo = GeoNames('http://thehistoryatlas.org')
    with pytest.raises(ConnectionError):
        geo.build()

# this requests real resources from the geonames server,
# so be very sparing in actually running this test.
@pytest.mark.skip('Pulls in resource from geonames.org -- only run if absolutely necessary')
def test_geonames(tmp_path):
    geo = GeoNames('https://download.geonames.org/export/dump/cities15000.zip')
    geo._basedir = ''   # NOTE: add a reasonable dir for your local system here
                        #       should probably discover the path in module anyways,
                        #       but for now can count on docker path being predictable 
    city_rows = geo.build()
    assert isinstance(city_rows, list)
    for r in city_rows:
        assert isinstance(r, CityRow)
        assert isinstance(r.name, str)
        assert isinstance(r.latitude, float)
        assert isinstance(r.longitude, float)
