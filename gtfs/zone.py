from .csvmodel import CsvModel, id_field

@CsvModel(None)
class Zone:
    zone_id: str = id_field()
