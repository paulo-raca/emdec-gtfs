# -*- coding: utf-8 -*-
import handlers
from handlers import JsonHandler
import json
import linhas
from gtfs import *
from StringIO import StringIO
from datetime import date, datetime, timedelta
from time import time as now
from google.appengine.ext import ndb
from google.appengine.api import taskqueue
import logging
from gcs_cache import GCSCached

def format_time(seconds):
    return '%02d:%02d:%02d' % (seconds // 3600, (seconds // 60) % 60, seconds % 60 )

def parse_time(t):
    parts = map(int, t.split(':'))
    if len(parts) == 2:
        parts.append(0)
    return parts[0]*3600 + parts[1]*60 + parts[2]

class RouteHandler(handlers.BaseRequestHandler):
    def parse_route_codes(self, route_codes):
        if route_codes=='all':
            return 'all', self.get_route_list()
        else:
            if isinstance(route_codes, basestring):
                route_codes = filter(None, map(str.strip, str(route_codes).split(',')))
            route_codes = sorted(route_codes)
            return ' '.join(route_codes), route_codes

    def gtfs_filename(self, name):
        return 'google_transit%s.zip' % ('' if name is 'all' else ' ' + name)

    @GCSCached()
    def get_route_info(self, route_codes, nocache=False):
        name, route_codes = self.parse_route_codes(route_codes)
        filename = '%s.json' % name
        if len(route_codes) == 1:
            f = lambda: {route_codes[0]: linhas.detalhes(route_codes[0])}
        else:
            f = lambda: {x: self.get_route_info(x)[x] for x in route_codes}

        return filename, f, nocache

    @GCSCached(content_type='application/zip', encode_contents=None, decode_contents=None)
    def get_gtfs(self, route_codes, nocache=False):
        name, _ = self.parse_route_codes(route_codes)
        return self.gtfs_filename(name), lambda: self.build_gtfs(self.get_route_info(route_codes)).getzip(), nocache

    @GCSCached()
    def get_route_list(self, nocache=False):
        return 'routes.json', linhas.linhas, nocache

    # ============= Handlers ===================

    def fetch_file(self, filename):
        self.serve_gcs(filename)

    @JsonHandler()
    def async(self, what):
        what = '/' + what
        taskqueue.add(url=what + '?nocache', method='GET')
        return "Queued %s" % what

    @JsonHandler()
    def async_refresh(self):
        all_routes = self.get_route_list(nocache=True)
        for route in all_routes:
            taskqueue.add(url='/export/%s?nocache' % route, method='GET')
            taskqueue.add(url='/export/%s/gtfs?nocache' % route, method='GET')
        taskqueue.add(url='/export/all?nocache', method='GET')
        taskqueue.add(url='/export/all/gtfs?nocache', method='GET')
        return "Queued everything uncached"

    @JsonHandler()
    def export_route_list(self):
        return self.get_route_list(nocache=self.request.get("nocache", None) is not None)

    @JsonHandler()
    def export_route_info(self, route_codes):
        return self.get_route_info(route_codes, nocache=self.request.get("nocache", None) is not None)

    def export_gtfs(self, route_codes):
        zip = self.get_gtfs(route_codes, nocache=self.request.get("nocache", None) is not None)

        name, _ = self.parse_route_codes(route_codes)
        self.response.headers['Content-Type'] = 'application/zip'
        self.response.headers['Content-Disposition'] = 'attachment; filename=%s' % self.gtfs_filename(name)
        self.response.write(zip)


    def get_agency(self):
        agency = Agency(
            key=ndb.Key(Agency, 'emdec'),
            agency_name='Emdec',
            agency_url='http://www.emdec.com.br/',
            agency_timezone='America/Sao_Paulo',
            agency_lang='pt',
            agency_phone='(19) 3772-1517',
            agency_fare_url='http://www.emdec.com.br/eficiente/sites/portalemdec/pt-br/site.php?secao=tarifas'
        )
        return agency

    def get_calendars(self):
        Y = Calendar.Available.AVAILABLE
        N = Calendar.Available.UNAVAILABLE
        calendars = {
            'all':       Calendar(monday=Y, tuesday=Y, wednesday=Y, thursday=Y, friday=Y, saturday=Y, sunday=Y ),
            'weekday':   Calendar(monday=Y, tuesday=Y, wednesday=Y, thursday=Y, friday=Y, saturday=N, sunday=N),
            'weekend':   Calendar(monday=N, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=Y, sunday=Y ),
            'monday':    Calendar(monday=Y, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=N, sunday=N),
            'tuesday':   Calendar(monday=N, tuesday=Y, wednesday=N, thursday=N, friday=N, saturday=N, sunday=N),
            'wednesday': Calendar(monday=N, tuesday=N, wednesday=Y, thursday=N, friday=N, saturday=N, sunday=N),
            'thursday':  Calendar(monday=N, tuesday=N, wednesday=N, thursday=Y, friday=N, saturday=N, sunday=N),
            'friday':    Calendar(monday=N, tuesday=N, wednesday=N, thursday=N, friday=Y, saturday=N, sunday=N),
            'saturday':  Calendar(monday=N, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=Y, sunday=N),
            'sunday':    Calendar(monday=N, tuesday=N, wednesday=N, thursday=N, friday=N, saturday=N, sunday=Y ),
        }
        for calendar_id, calendar in calendars.iteritems():
            calendar.key = ndb.Key(Calendar, calendar_id)
            calendar.start_date = date.today() - timedelta(days=1)
            calendar.end_date   = date.today() + timedelta(days=90)
        return calendars

    def get_feed_info(self):
        return FeedInfo(
            feed_publisher_name='Paulo Costa',
            feed_publisher_url='https://github.com/paulo-raca/Emdec-GTransit',
            feed_lang='pt',
            feed_start_date=None,
            feed_end_date=None,
            feed_version=datetime.now().isoformat()
        )

    def get_fare(self):
        return Fare(
            key=ndb.Key(Fare, 'normal fare'),
            price=3.50,
            currency_type='BRL',
            payment_method=Fare.PaymentMethod.ONBOARD,
            transfers=None, # UNLIMITED
            transfer_duration=2*60*60,
            rules=[] # No rules, this fare applies to all trips
        )

    def build_gtfs(self, route_infos):
        export = GTFS()

        export.write(self.get_feed_info())
        export.write(self.get_fare())
        calendars = self.get_calendars()
        agency = self.get_agency()
        export.write(agency)
        for calendar in calendars.itervalues():
            export.write(calendar)

        for route_code, raw_route in route_infos.iteritems():
            route_begin_time = now()

            #logging.info('Fetched Route %s' % route_code)
            route = Route(
                key=ndb.Key(Route, route_code),
                agency_id=agency.key,
                route_short_name=raw_route['route_short_name'],
                route_long_name=raw_route['route_long_name'],
                route_desc=(raw_route['comments'] or '').replace('\n', ' '),  # FIXME Not really a description
                route_type=Route.Type.BUS,
                route_url=raw_route['route_url'],
                route_color=raw_route['route_color'],
                route_text_color=raw_route['route_text_color'],
            )
            export.write(route)

            for (direction, trip_direction) in zip(raw_route['directions'], [Trip.Direction.A, Trip.Direction.B]):
                shape = Shape(
                    key=ndb.Key(Shape, route_code + ':' + str(trip_direction)),
                    shape_points=[]
                )
                for raw_vertex in direction['map']['shape']:
                    shape.shape_points.append(ShapePoint(
                        shape_pt_latlon=ndb.GeoPt(*raw_vertex['latlng']),
                        shape_dist_traveled = raw_vertex['shape_dist']
                    ))
                export.write(shape)


                expected_duration = (direction['details']['Tempo de Percurso'] or '60').split(' a ')
                expected_duration = 60 * (int(expected_duration[0]) + int(expected_duration[-1])) / 2

                stops_times = []
                for raw_stop in direction['map']['stops']:
                    stop = Stop(
                        key=ndb.Key(Stop, '%f,%f' % (raw_stop['latlng'][0], raw_stop['latlng'][1])),
                        stop_code=None,
                        stop_name=raw_stop['name'],
                        stop_latlon=ndb.GeoPt(*raw_stop['latlng']),
                        stop_desc=None,
                        zone_id=None,
                        stop_url=None,
                        location_type=Stop.LocationType.STOP,
                        parent_station=None,
                        stop_timezone=None,
                        wheelchair_boarding=None,
                    )
                    export.write(stop)
                    stops_times.append(StopTime(
                        arrival_time=None,
                        departure_time=None,
                        stop_id=stop.key,
                        stop_headsign=None, #FIXME - Override halfway on 2way routes
                        pickup_type=StopTime.PickupDropoffType.AVAILABLE,
                        drop_off_type=StopTime.PickupDropoffType.AVAILABLE,
                        shape_dist_traveled=raw_stop['shape_dist'],
                        timepoint = StopTime.TimePoint.APPROXIMATE
                    ))

                for schedule_name in direction['schedules'].iterkeys():
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
                    stops_times[0].populate(
                        timepoint=StopTime.TimePoint.EXACT,
                        arrival_time=format_time(times[0]),
                        departure_time=format_time(times[0]),
                    )
                    stops_times[-1].populate(
                        timepoint = StopTime.TimePoint.APPROXIMATE,
                        arrival_time=format_time(times[0] + expected_duration),
                        departure_time=format_time(times[0] + expected_duration),
                    )

                    # frequency-based records ==================
                    frequencies = []
                    for i in range(len(times)-1):
                        frequency = TripFrequency(
                            start_time=format_time(times[i]),
                            end_time=format_time(times[i+1]),
                            headway_secs=times[i+1] - times[i],
                            exact_times=TripFrequency.ExactTime.EXACT
                        )
                        #Merge with previous range
                        if frequencies and frequency.start_time == frequencies[-1].end_time and frequency.headway_secs == frequencies[-1].headway_secs:
                            frequencies[-1].end_time = frequency.end_time
                        #Add a new range
                        else:
                            frequencies.append(frequency)

                    #End time is not inclusive - Last end_time must be greater than last trip's time
                    if frequencies:
                        frequencies[-1].end_time = format_time(times[-1]+1)

                    trip = Trip(
                        key=ndb.Key(Trip, route_code + ':' + str(trip_direction) + ':' + schedule_name),
                        route_id=route.key,
                        service_id=calendars[schedule_name].key,
                        trip_headsign=direction['details']['Letreiro'],
                        direction_id=trip_direction,
                        shape_id=shape.key,
                        stop_times=stops_times,
                        frequencies=frequencies,
                        wheelchair_accessible=None, # FIXME: Tenho essa informação, mas estou gerando um único 'Trip' para todo o
                        bikes_allowed=Trip.BikesAllowed.NOT_ALLOWED,
                    )
                    export.write(trip)

                    # Time-based records ==================
                    #for time in times:
                        ##We set departure time to "zero" (We use Frequencies.txt, therefore this is a relative time)
                        #stops_times[0].populate(
                            #timepoint=StopTime.TimePoint.EXACT,
                            #arrival_time=format_time(time),
                            #departure_time=format_time(time),
                        #)
                        ##We set arrival time to the estimated trip time (We use Frequencies.txt, therefore this is a relative time)
                        #stops_times[-1].populate(
                            #timepoint = StopTime.TimePoint.APPROXIMATE,
                            #arrival_time=format_time(time + expected_duration),
                            #departure_time=format_time(time + expected_duration),
                        #)

                        #trip = Trip(
                            #key=ndb.Key(Trip, route_code + ':' + str(trip_direction) + ':' + schedule_name + '@' + format_time(time)),
                            #route_id=route.key,
                            #service_id=calendars[schedule_name].key,
                            #trip_headsign=direction['details']['Letreiro'],
                            #direction_id=trip_direction,
                            #shape_id=shape.key,
                            #stop_times=stops_times,
                            ##frequencies=frequencies,
                            #wheelchair_accessible=None, # FIXME: Tenho essa informação, mas estou gerando um único 'Trip' para todo o
                            #bikes_allowed=Trip.BikesAllowed.NOT_ALLOWED,
                        #)
                        #export.write(trip)
            logging.info('Exported Route %s - %.2fs' % (route_code, (now() - route_begin_time)))
        logging.info('Export completed')
        return export
