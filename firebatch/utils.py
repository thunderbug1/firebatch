import json
import re
from typing import Any, List, TextIO, Tuple
from google.cloud.firestore import Client
import logging
logger = logging.getLogger(__name__)

def read_documents(file: TextIO, format="auto"):
    """ Reads the firestore documents from either a json or a jsonl file. 
        The json file may be formatted as a list of firestore documents or as a single firestore document."""
    # Try to parse the entire file as JSON
    def read_json(file: TextIO):
        file.seek(0)  # Ensure we start at the beginning
        data = json.load(file)
        if isinstance(data, list):
            return data
        return [data] # if it is just one object, wrap it as a list
    
    def read_jsonl(file: TextIO):
        file.seek(0)  # Reset the file position to the beginning
        data = []
        for line in file:
            sripped_line = line.strip()
            if sripped_line:  # Only consider non-empty lines
                data.append(json.loads(sripped_line))  # Attempt to parse line as JSON
        return data  # Assume JSONL if no exceptions were raised for non-empty lines

    if format == "auto":
        try:
            return read_json(file)
        except json.JSONDecodeError:
            # If JSON parsing fails, proceed to check for JSONL
            try:
                return read_jsonl(file)
            except json.JSONDecodeError:
                raise Exception("Unknown file format, could not detect either JSON or JSONL.")
    elif format == "json":
        return read_json(file)
    elif format == "jsonl":
        return read_jsonl(file)
    
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