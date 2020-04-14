from gtfs import *
from datetime import date, datetime, timedelta
from time import time as now
import logging

def format_time(seconds):
    return '%02d:%02d:%02d' % (seconds // 3600, (seconds // 60) % 60, seconds % 60 )

def parse_time(t):
    parts = [int(x) for x in t.split(':')]
    if len(parts) == 2:
        parts.append(0)
    return parts[0]*3600 + parts[1]*60 + parts[2]

#def parse_route_codes(self, route_codes):
    #if route_codes=='all':
        #return 'all', get_route_list()
    #else:
        #if isinstance(route_codes, basestring):
            #route_codes = filter(None, map(str.strip, str(route_codes).split(',')))
        #route_codes = sorted(route_codes)
        #return '_'.join(sorted(route_codes)), route_codes

#def gtfs_filename(self, name):
    #return 'google_transit%s.zip' % ('' if name is 'all' else '_' + name)

#@GCSCached()
#def get_single_route_info(self, route_code, nocache=False):
    #filename = '%s.json' % route_code
    #f = lambda: linhas.detalhes(route_code)
    #return filename, f, nocache

#def get_multi_route_info(self, name, route_codes, nocache=False):
    #for x in route_codes:
        #yield (x, get_single_route_info(x, nocache=nocache))

#@GCSCached(content_type='application/zip', encode_contents=None, decode_contents=None)
#def get_gtfs(self, name, route_codes, nocache=False):
    #filename = 'gtfs_%s.zip' % name
    #f = lambda: build_gtfs(get_multi_route_info(name, route_codes)).getzip()
    #return filename, f, nocache

#@GCSCached()
#def get_route_list(self, nocache=False):
    #return 'routes.json', linhas.linhas, nocache

## ============= Handlers ===================

#def fetch_file(self, filename):
    #serve_gcs(filename)

#@JsonHandler()
#def async(self, what):
    #what = '/' + what
    #taskqueue.add(url=what + '?nocache', method='GET')
    #return "Queued %s" % what

#@JsonHandler()
#def async_refresh(self):
    #all_routes = get_route_list(nocache=True)
    #for route in all_routes:
        #taskqueue.add(url='/route/%s/json?nocache' % route, method='GET')
        #taskqueue.add(url='/route/%s/gtfs?nocache' % route, method='GET')
    #taskqueue.add(url='/route/all/gtfs?nocache', method='GET')
    #return "Queued everything uncached"

#@JsonHandler()
#def export_route_list(self):
    #return get_route_list(nocache=request.get("nocache", None) is not None)

#@JsonHandler()
#def export_route_info(self, route_codes):
    #name, codes = parse_route_codes(route_codes)
    #return OrderedDict(get_multi_route_info(name, codes, nocache=request.get("nocache", None) is not None))

#def export_gtfs(self, route_codes):
    #name, codes = parse_route_codes(route_codes)
    #zip = get_gtfs(name, codes, nocache=request.get("nocache", None) is not None)

    #response.headers['Content-Type'] = 'application/zip'
    #response.headers['Content-Disposition'] = 'attachment; filename=%s' % gtfs_filename(name)
    #response.write(zip)


def get_agency():
    agency = Agency(
        agency_id='emdec',
        agency_name='Emdec',
        agency_url='http://www.emdec.com.br/',
        agency_timezone='America/Sao_Paulo',
        agency_lang='pt',
        agency_phone='(19) 3772-1517',
        agency_fare_url='http://www.emdec.com.br/eficiente/sites/portalemdec/pt-br/site.php?secao=tarifas'
    )
    return agency

def get_calendars():
    Y = Calendar.Available.Available
    N = Calendar.Available.Unavailable
    calendars = [
        Calendar('all',       monday=Y, tuesday=Y, wednesday=Y, thursday=Y, friday=Y, saturday=Y, sunday=Y ),
        Calendar('weekday',   monday=Y, tuesday=Y, wednesday=Y, thursday=Y, friday=Y, saturday=N, sunday=N),
        Calendar('weekend',   monday=N, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=Y, sunday=Y ),
        Calendar('monday',    monday=Y, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=N, sunday=N),
        Calendar('tuesday',   monday=N, tuesday=Y, wednesday=N, thursday=N, friday=N, saturday=N, sunday=N),
        Calendar('wednesday', monday=N, tuesday=N, wednesday=Y, thursday=N, friday=N, saturday=N, sunday=N),
        Calendar('thursday',  monday=N, tuesday=N, wednesday=N, thursday=Y, friday=N, saturday=N, sunday=N),
        Calendar('friday',    monday=N, tuesday=N, wednesday=N, thursday=N, friday=Y, saturday=N, sunday=N),
        Calendar('saturday',  monday=N, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=Y, sunday=N),
        Calendar('sunday',    monday=N, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=N, sunday=Y ),
    ]

    for calendar in calendars:
        calendar.start_date = date.today() - timedelta(days=1)
        calendar.end_date   = date.today() + timedelta(days=90)

    return {
        calendar.service_id: calendar
        for calendar in calendars
    }

def get_feed_info():
    return FeedInfo(
        feed_publisher_name='Paulo Costa',
        feed_publisher_url='https://github.com/paulo-raca/emdec-gtfs',
        feed_lang='pt',
        feed_start_date=None,
        feed_end_date=None,
        feed_version=datetime.now().isoformat()
    )

def get_fare():
    return Fare(
        fare_id='normal fare',
        price=4.95,
        currency_type='BRL',
        payment_method=Fare.PaymentMethod.ONBOARD,
        transfers=None, # UNLIMITED
        transfer_duration=2*60*60,
        rules=[] # No rules, this fare applies to all trips
    )

def build_gtfs(route_infos):
    begin_time = now()
    export = GTFS()

    export.write(get_feed_info())
    export.write(get_fare())
    calendars = get_calendars()
    agency = get_agency()

    for route_code, raw_route in route_infos.items():
        route_begin_time = now()

        route = Route(
            route_id=route_code,
            agency_id=agency,
            route_short_name=raw_route['route_short_name'],
            route_long_name=raw_route['route_long_name'],
            route_desc=(raw_route['comments'] or '').replace('\n', ' '),  # FIXME Not really a description
            route_type=Route.Type.Bus,
            route_url=raw_route['route_url'],
            route_color=raw_route['route_color'],
            route_text_color=raw_route['route_text_color'],
        )

        for (direction, trip_direction) in zip(raw_route['directions'], [Trip.Direction.A, Trip.Direction.B]):
            shape = Shape(
                shape_id=f'{route_code}:{trip_direction.name}',
                shape_points=[]
            )
            for raw_vertex in direction['map']['shape']:
                shape.shape_points.append(ShapePoint(
                    shape_pt_latlon=LatLon(*raw_vertex['latlng']),
                    shape_dist_traveled = raw_vertex['shape_dist']
                ))

            expected_duration = (direction['details']['Tempo de Percurso'] or '60').split(' a ')
            expected_duration = 60 * (int(expected_duration[0]) + int(expected_duration[-1])) / 2

            stops_times = []
            for raw_stop in direction['map']['stops']:
                stop = Stop(
                    stop_id=f"{raw_stop['latlng'][0]},{raw_stop['latlng'][1]}",
                    stop_code=None,
                    stop_name=raw_stop['name'],
                    stop_latlon=LatLon(*raw_stop['latlng']),
                    stop_desc=None,
                    zone_id=None,
                    stop_url=None,
                    location_type=Stop.LocationType.Stop,
                    parent_station=None,
                    stop_timezone=None,
                    wheelchair_boarding=None,
                )
                stops_times.append(StopTime(
                    arrival_time=None,
                    departure_time=None,
                    stop_id=stop,
                    stop_headsign=None, #FIXME - Override halfway on 2way routes
                    pickup_type=StopTime.PickupDropoffType.Available,
                    drop_off_type=StopTime.PickupDropoffType.Available,
                    shape_dist_traveled=raw_stop['shape_dist'],
                    timepoint = StopTime.TimePoint.Approximate
                ))

            for schedule_name in direction['schedules'].keys():
                # Convert trip times into frequencies -- Assumes at least 2 trips/day
                times = []
                for raw_trip in direction['schedules'][schedule_name]['trips']:
                    time = parse_time(raw_trip['time'])
                    if times:
                        while time < times[-1]:
                            time += 24*60*60

                    # Algumas linhas possuem várias saídas no mesmo horário (119 - TERM OURO VERDE EXPRESSA)
                    # Isso complica um pouco a minha vida, então eu removo as duplicadas
                    if not times or time != times[-1]:
                        times.append(time)

                #Set departure and arrival times
                stops_times[0].timepoint=StopTime.TimePoint.Exact
                stops_times[0].arrival_time=format_time(times[0])
                stops_times[0].departure_time=format_time(times[0])

                stops_times[-1].timepoint = StopTime.TimePoint.Approximate
                stops_times[-1].arrival_time=format_time(times[0] + expected_duration)
                stops_times[-1].departure_time=format_time(times[0] + expected_duration)


                # frequency-based records ==================
                frequencies = []
                for i in range(len(times)-1):
                    frequency = TripFrequency(
                        start_time=format_time(times[i]),
                        end_time=format_time(times[i+1]),
                        headway_secs=times[i+1] - times[i],
                        exact_times=TripFrequency.ExactTime.Approximate
                    )
                    if frequencies and frequency.start_time == frequencies[-1].end_time and frequency.headway_secs == frequencies[-1].headway_secs:
                        #Merge with previous range
                        frequencies[-1].end_time = frequency.end_time
                    else:
                        #Add a new range
                        frequencies.append(frequency)

                #End time is not inclusive - Last end_time must be greater than last trip's time
                if frequencies:
                    frequencies[-1].end_time = format_time(times[-1]+1)

                trip = Trip(
                    trip_id=f"{route_code}:{trip_direction.name}:{schedule_name}",
                    route_id=route,
                    service_id=calendars[schedule_name],
                    trip_headsign=direction['details']['Letreiro'],
                    direction_id=trip_direction,
                    shape_id=shape,
                    stop_times=stops_times,
                    frequencies=frequencies,
                    wheelchair_accessible=None, # FIXME: Tenho essa informação, mas estou gerando um único 'Trip' para todo o
                    bikes_allowed=Trip.BikesAllowed.NotAllowed,
                )
                export.write(trip)

        print(f'Exported Route {route_code}: {now() - route_begin_time:.2f}s')
    print(f'Export completed: {now() - begin_time:.2f}s')
    return export
