import datetime as dt

from src.evaluation.known_events import KNOWN_EXTREME_EVENTS


def test_known_events_have_required_fields_and_valid_dates():
    required_keys = {"name", "region", "start_date", "end_date", "source"}
    assert len(KNOWN_EXTREME_EVENTS) >= 8

    for event in KNOWN_EXTREME_EVENTS:
        assert required_keys.issubset(event.keys())
        start = dt.date.fromisoformat(event["start_date"])
        end = dt.date.fromisoformat(event["end_date"])
        assert start <= end


def test_known_events_are_scoped_to_rmr():
    assert all(event["region"] == "rmr" for event in KNOWN_EXTREME_EVENTS)
