import json
import re
from typing import Any, List, TextIO, Tuple
from google.cloud.firestore import Client
import logging
logger = logging.getLogger(__name__)

def detect_file_format(file : TextIO) -> str:
    # Auto-detect file format
    if isinstance(file, str):
        return 'json'
    else:
        return 'jsonl'

    # first_line = file.readline()
    # try:
    #     # Try to parse the first line as JSON
    #     json.loads(first_line)
    #     input_format = 'jsonl'  # Successfully parsed a single line as JSON
    # except json.JSONDecodeError:
    #     input_format = 'json'  # If it fails, assume the whole file is a single JSON array

    # # Since we read the first line to detect the format, we need to ensure it's not lost
    # file.seek(0)  # Reset file pointer to the start for re-reading
    # return input_format

def get_nested_collection_reference(db: Client, collection_path: str):
    # Splits the collection path and returns the final reference
    ref = db
    parts = collection_path.split('/')
    for i, part in enumerate(parts):
        if i % 2 == 0:
            ref = ref.collection(part)
        else:
            ref = ref.document(part)
    return ref

def parse_query_condition(condition: str) -> Tuple[str, str, Any]:
    """Parses a query condition, allowing spaces around operators."""
    # List of Firestore operators for pattern matching
    logger.debug(f"evaluate condition: {condition}")
    operators = [">=", "<=", "==", "!=", ">", "<", "array-contains", "in", "array-contains-any"]
    
    # Create a regex pattern to match any operator from the list, allowing spaces around it
    operators_regex = '|'.join([re.escape(op) for op in operators])
    pattern = rf'([^:]+)\s*({operators_regex})\s*(.+)'
    
    match = re.match(pattern, condition)
    if not match:
        raise ValueError(f"Invalid query condition: '{condition}'. Must be in 'field operator value' format.")
    
    field, operator, value = match.groups()
    field = field.strip()
    # Convert value from string to correct type (int, float, bool, etc.)
    if value.isdigit():
        value = int(value)
    elif value.replace('.', '', 1).isdigit():
        value = float(value)
    elif value.lower() in ['true', 'false']:
        value = value.lower() == 'true'
    # Add more conversions as necessary, e.g., for dates or arrays
    
    return field, operator, value

def validate_queries(ctx, param, value: List[str]) -> List[Tuple[str, str, Any]]:
    """Validates and parses query conditions provided through --where options."""
    queries = []
    for cond in value:
        queries.append(parse_query_condition(cond))
    return queries