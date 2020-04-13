from .gtfs import GTFS
from .stop import Stop
print(GTFS())
print(Stop())

gtfs = GTFS()
stop1 = Stop(stop_id="foo")
stop2 = Stop(stop_id="bar", location_type=Stop.LocationType.Station)
stop1.parent_station = stop2
gtfs.write(stop1)
print(gtfs.getvalue())
