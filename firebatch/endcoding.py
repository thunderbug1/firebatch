
import json
import re
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from google.cloud.firestore_v1 import GeoPoint, DocumentReference
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

ISO8601_REGEX = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.\d+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'

class FirestoreEncoder(json.JSONEncoder):
    def __init__(self, *args, timestamp_convert=False, geopoint_convert=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp_convert = timestamp_convert
        self.geopoint_convert = geopoint_convert

    def default(self, obj):
        if isinstance(obj, DatetimeWithNanoseconds):
            if self.timestamp_convert:
                return obj.isoformat()
            return {'__timestamp__': obj.isoformat()}
        if isinstance(obj, GeoPoint):
            if self.geopoint_convert:
                return {'latitude': obj.latitude, 'longitude': obj.longitude}
            return {"__geopoint__": {'latitude': obj.latitude, 'longitude': obj.longitude}}
        elif isinstance(obj, DocumentReference):
            return {'__doc_ref__': str(obj.path)}
        # Let the base class default method raise the TypeError
        return super().default(obj)

def firestore_encoder_factory(timestamp_convert=False, geopoint_convert=False):
    """
    A factory function that creates and returns a callable which itself
    returns an instance of FirestoreEncoder configured with the given parameters.

    Args:
        timestamp_convert (bool): If True, convert timestamp objects to ISO format.
        geopoint_convert (bool): If True, convert GeoPoint objects to a dict with 'latitude' and 'longitude'.

    Returns:
        Callable: A callable object that, when called, returns an instance of FirestoreEncoder.
    """
    # The actual callable that `json.dumps` will use to get an encoder instance
    def encoder_callable(*args, **kwargs):
        return FirestoreEncoder(timestamp_convert=timestamp_convert, geopoint_convert=geopoint_convert, *args, **kwargs)

    return encoder_callable

    
def to_json(documents: list, indent=None, timestamp_convert=False, geopoint_convert=False) -> str:
    encoder_callable = firestore_encoder_factory(timestamp_convert=timestamp_convert, geopoint_convert=geopoint_convert)
    return json.dumps(documents, cls=encoder_callable, indent=indent)


def convert_to_firestore_types(db, data, timestamp_convert, geopoint_convert):
    """Recursively convert known structures from JSON data to Firestore data types."""
    if isinstance(data, dict):
        if geopoint_convert and 'latitude' in data and 'longitude' in data and len(data) == 2:
            return GeoPoint(data['latitude'], data['longitude'])
        elif '__geopoint__' in data and len(data) == 1:
            geodata = data['__geopoint__']
            return GeoPoint(geodata['latitude'], geodata['longitude'])
        elif '__timestamp__' in data and len(data) == 1:
            return datetime.fromisoformat(data['__timestamp__'])
        elif '__doc_ref__' in data and len(data) == 1:
            return db.document(data['__doc_ref__'])
        return {key: convert_to_firestore_types(db, value, timestamp_convert, geopoint_convert) for key, value in data.items()}
    elif timestamp_convert and isinstance(data, str) and re.match(ISO8601_REGEX, data): # auto convert isotimestamps to firestore Timestamp
        return datetime.fromisoformat(data)
    elif isinstance(data, list):
        return [convert_to_firestore_types(db, item, timestamp_convert, geopoint_convert) for item in data]
    return data