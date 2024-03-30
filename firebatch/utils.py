import json
import re
from typing import Any, List, TextIO, Tuple
from google.cloud.firestore import Client
import logging
logger = logging.getLogger(__name__)

def detect_file_format(file: TextIO):
    # Read a reasonable amount of data to guess the file format
    first_chunk = file.read(1024)
    file.seek(0)  # Reset file pointer to the start for re-reading

    # Try to detect if it's a JSONL file
    if first_chunk.strip().startswith('{') and "\n" in first_chunk:
        # Check if each line is a valid JSON
        for line in first_chunk.splitlines():
            try:
                json.loads(line)
            except json.JSONDecodeError:
                break
        else:
            # If all lines in the first chunk are valid JSON, it's likely a JSONL file
            return 'jsonl'

    # Try to parse the chunk as JSON
    try:
        json.loads(first_chunk)
        return 'json'
    except json.JSONDecodeError:
        pass

    # Default to unknown if no format matches
    return 'unknown'

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
    """Parses a query condition, allowing spaces around operators and handling quoted strings as values."""
    logger.debug(f"Evaluating condition: {condition}")
    # List of Firestore operators for pattern matching
    operators = [">=", "<=", "==", "!=", ">", "<", "array-contains", "in", "array-contains-any"]
    
    # Create a regex pattern to match any operator from the list, allowing spaces around it
    operators_regex = '|'.join([re.escape(op) for op in operators])
    pattern = rf'([^:]+?)\s*({operators_regex})\s*(.+)'  # Non-greedy match for the field
    
    match = re.match(pattern, condition)
    if not match:
        raise ValueError(f"Invalid query condition: '{condition}'. Must be in 'field operator value' format.")
    
    field, operator, value = match.groups()
    field = field.strip()

    # Handle quoted string values
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]  # Strip the quotes
    else:
        # Convert value from string to correct type (int, float, bool, etc.)
        if value.isdigit():
            value = int(value)
        elif re.match(r'^-?\d+(\.\d+)?$', value):  # Matches float numbers
            value = float(value)
        elif value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        # Add additional type conversions as necessary, e.g., for dates or arrays
    
    return field, operator, value

def validate_queries(ctx, param, value: List[str]) -> List[Tuple[str, str, Any]]:
    """Validates and parses query conditions provided through --where options."""
    queries = []
    for cond in value:
        queries.append(parse_query_condition(cond))
    return queries