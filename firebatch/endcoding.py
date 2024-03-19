
import json
import re
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from google.cloud.firestore_v1 import GeoPoint, DocumentReference
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

ISO8601_REGEX = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.\d+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'

class FirestoreEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DatetimeWithNanoseconds):
            return obj.isoformat()
        if isinstance(obj, GeoPoint):
            return {'latitude': obj.latitude, 'longitude': obj.longitude}
        elif isinstance(obj, DocumentReference):
            return {'__doc_ref__': str(obj.path)}
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
    
def to_json(documents: list, indent=None) -> str:
    return json.dumps(documents, cls=FirestoreEncoder, indent=indent)


def convert_to_firestore_types(db, data):
    """Recursively convert known structures from JSON data to Firestore data types."""
    if isinstance(data, dict):
        if 'latitude' in data and 'longitude' in data and len(data) == 2:
            return GeoPoint(data['latitude'], data['longitude'])
        elif '__doc_ref__' in data:
            return db.document(data['__doc_ref__'])
        return {key: convert_to_firestore_types(db, value) for key, value in data.items()}
    elif isinstance(data, str) and re.match(ISO8601_REGEX, data): # auto convert isotimestamps to firestore Timestamp
        return datetime.fromisoformat(data)
    elif isinstance(data, list):
        return [convert_to_firestore_types(db, item) for item in data]
    return data