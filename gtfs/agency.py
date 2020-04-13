from .csvmodel import CsvModel, id_field

@CsvModel('agency.txt')
class Agency:
    agency_id: str = id_field()
    agency_name: str = None
    agency_url: str = None
    agency_timezone: str = None
    agency_lang: str = None
    agency_phone: str = None
    agency_fare_url: str = None
