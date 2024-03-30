import json
import re
from typing import Any, List, TextIO, Tuple
from google.cloud.firestore import Client
import logging
logger = logging.getLogger(__name__)

def detect_file_format(file: TextIO):
    # Read the first 5 lines or until the file ends
    lines = [file.readline() for _ in range(5)]
    file.seek(0)  # Reset file pointer to the start for re-reading

    # Remove empty lines that could occur if the file has fewer than 5 lines
    lines = [line for line in lines if line.strip()]

    # If there are no lines, we cannot determine the format
    if not lines:
        raise Exception("File is empty or does not contain readable content.")

    # Try to detect if it's a JSONL file by checking if each of the first 5 lines is a valid JSON
    is_jsonl = True
    for line in lines:
        try:
            json.loads(line)
        except json.JSONDecodeError:
            is_jsonl = False
            break

    if is_jsonl:
        return 'jsonl'

    # If not JSONL, try to parse the combined lines as JSON
    combined_lines = ''.join(lines)
    try:
        json.loads(combined_lines)
        return 'json'
    except json.JSONDecodeError:
        pass

    # Default to unknown if no format matches
    raise Exception("Unknown file format, could not detect either JSON or JSONL.")

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