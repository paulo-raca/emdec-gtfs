from datetime import date
from enum import Enum
from .csvmodel import CsvModel, id_field

@CsvModel('calendar.txt')
class Calendar:
    class Available(Enum):
        Unavailable = 0
        Available = 1

    service_id: str = id_field()
    monday: Available = None
    tuesday: Available = None
    wednesday: Available = None
    thursday: Available = None
    friday: Available = None
    saturday: Available = None
    sunday: Available = None
    start_date: date = None
    end_date: date = None
