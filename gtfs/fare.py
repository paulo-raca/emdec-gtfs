from enum import Enum
from .csvmodel import CsvModel, child_parent_field, reference_field, children_list_field, id_field
from .zone import Zone
from .route import Route
from typing import List

@CsvModel('fare_rules.txt')
class FareRule:
    fare_id: "Fare" = child_parent_field()
    route_id: Route = reference_field()
    origin_id: Zone = reference_field()
    destination_id: Zone = reference_field()
    contains_id: Zone = reference_field()

@CsvModel('fare_attributes.txt')
class Fare:
    class PaymentMethod(Enum):
        ONBOARD = 0
        BEFORE_BOARDING = 1
    fare_id: str = id_field()
    price: float = None
    currency_type: str = None
    payment_method: PaymentMethod = None
    transfers: int = None
    transfer_duration: int = None
    rules: List[FareRule] = children_list_field()
