from app.risk import calculate_los_risk
from app.models import Encounter
from datetime import date


class DummyEncounter2:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


def test_los_short():
    enc = DummyEncounter2(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
    )
    los_days, los_level = calculate_los_risk(enc)
    assert los_days == 1
    assert los_level == "short"


def test_los_long():
    enc = DummyEncounter2(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 15),
    )
    los_days, los_level = calculate_los_risk(enc)
    assert los_days == 14
    assert los_level == "long"
