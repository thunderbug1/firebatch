from typing import Any, Optional
import click
import sys
import json
import importlib
import logging
from firebatch.operations import download_collection_documents, write_documents, delete_documents_in_firestore 
from firebatch.operations import process_deletion_file, update_documents_in_firestore, list_firestore_collections
from firebatch.utils import detect_file_format, validate_queries

try:
    from pydantic import ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    ValidationError = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class StdCommand(click.Command):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.params.insert(0, click.Option(['--debug'], is_flag=True, help='Enables debug mode.'))
        self.params.insert(1, click.Option(['--verbose', '-v'], is_flag=True, help='Enables verbose mode.'))
        self.params.insert(2, click.Option(['--dry-run', '-d'], is_flag=True, help='Runs the command without making any changes.'))
        self.params.insert(3, click.Option(['--collection', '-c'], required=True, help='Firestore collection path (e.g., "users/user_id/orders").'))

    def invoke(self, ctx: click.Context) -> Optional[Any]:
        debug = ctx.params.get('debug')
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
        
        ctx.params.pop('debug', None)  # Remove debug so it's not passed to commands
        
        # Continue with the standard command invocation
        return super().invoke(ctx)

def ensure_pydantic():
    if not PYDANTIC_AVAILABLE:
        logging.error("Pydantic not available, please install it with 'pip install firebatch[validation]'")
        sys.exit(1)

def load_validator(validator):
    """Dynamically loads a Pydantic model class from a string."""
    ensure_pydantic()
    if validator:
        module_name, class_name = validator.rsplit(':', 1)
        try:
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logging.error(f"Validator loading error: {e}")
            sys.exit(1)
    return None

def validate_data(data, validator_class):
    """Validates data using the provided Pydantic model class."""
    ensure_pydantic()
    if validator_class:
        try:
            # Validate using Pydantic model
            return validator_class.parse_raw(data)
        except ValidationError as e:
            logging.error(f"Data validation error: {e}")
            sys.exit(1)
    else:
        # Fallback to regular JSON parsing if no validator is provided
        return json.loads(data)

@click.group()
def cli():
    """Overview:
The Firebatch CLI is a command-line interface tool designed for batch operations on Google Firestore databases. It supports various operations such as reading, writing, updating, and deleting Firestore documents, with additional functionalities to handle Firestore specific data types like timestamps and geopoints. It's built to handle operations in bulk, making it ideal for migrations, backups, and batch modifications.

Usage:
firebatch [OPTIONS] COMMAND [ARGS]...
"""
    pass

@cli.command(cls=StdCommand)
@click.option('--format', '-f', type=click.Choice(['json', 'jsonl']), default='jsonl', help='Output format for reading documents.')
@click.option('--timestamp-convert', '-t', is_flag=True, help='convert firestore timestamps to simple datetime string in isoformat, otherwise the value will be wrapped with the key __timestamp__ for converting it back when writing.')
@click.option('--geopoint-convert', '-g', is_flag=True, help='convert geopoints to simple map with longitude and latitude, otherwise the values will be wrapped with the key __geopoint__ for converting it back when writing.')
@click.option('--raw', is_flag=True, default=False, help='disable the document ids in the output json and only output the data.')
@click.option('--where', '-w', multiple=True, callback=validate_queries, help='Query conditions (can specify multiple), formatted as "field operator value".')
@click.option('--order-by', help='Field to order the results by.')
@click.option('--limit', type=int, help='Limit the number of results.')
def read(collection, format, timestamp_convert, geopoint_convert, where, order_by, limit, verbose, raw, dry_run):
    read_documents = download_collection_documents(collection_path=collection, 
                                                   output_format=format,
                                                   timestamp_convert=timestamp_convert,
                                                   geopoint_convert=geopoint_convert,
                                                   conditions=where,
                                                   order_by=order_by,
                                                   limit=limit, 
                                                   raw=raw, 
                                                   verbose=verbose)
    print(read_documents)

@cli.command(cls=StdCommand)
@click.option('--timestamp-field', default=None, help='name of the field to set a server timestamp of insertion.')
@click.option('--format', type=click.Choice(['json', 'jsonl', 'auto']), default="auto", help='name of the field to set a server timestamp of insertion.')
@click.option('--timestamp-convert', '-t', is_flag=True, help='auto detect timestamps (datetime string in isoformat) and convert them to firebase Timestamp type.')
@click.option('--geopoint-convert', '-g', is_flag=True, help='auto detect geopoints (map with only longitude and latitude) and convert them to firebase GeoPoint type.')
@click.argument('file', type=click.File('r'), required=True)
def write(collection, file, timestamp_field, timestamp_convert, geopoint_convert, format, verbose, dry_run):
    write_documents(collection_path=collection, 
                    file=file, 
                    timestamp_field=timestamp_field, 
                    timestamp_convert=timestamp_convert,
                    geopoint_convert=geopoint_convert,
                    format=format, 
                    verbose=verbose, 
                    dry_run=dry_run)

@cli.command(cls=StdCommand)
@click.option('--validator', help='Validator module and class name (e.g., "my_validators:MyValidatorClass").')
@click.option('--upsert', is_flag=True, default=False, help='if true, inserts documents if they do not exist')
@click.option('--timestamp-field', default=None, help='Name of the field to set a server timestamp of update.')
@click.option('--timestamp-convert', '-t', is_flag=True, help='auto detect timestamps (datetime string in isoformat) and convert them to firebase Timestamp type.')
@click.option('--geopoint-convert', '-g', is_flag=True, help='auto detect geopoints (map with only longitude and latitude) and convert them to firebase GeoPoint type.')
@click.argument('file', type=click.File('r'), required=True)
def update(collection, validator, file, timestamp_field, timestamp_convert, geopoint_convert, upsert, verbose, dry_run):
    input_format = detect_file_format(file)
    if input_format == 'json':
        updates = json.load(file)
    else:
        updates = [json.loads(line) for line in file]

    # Optional: Validate each update data using Pydantic if validator is provided
    if validator:
        validator_class = load_validator(validator)
        updates = [validate_data(json.dumps(update), validator_class) for update in updates]

    update_documents_in_firestore(collection_path=collection, 
                                  updates=updates, 
                                  timestamp_field=timestamp_field,
                                  timestamp_convert=timestamp_convert,
                                  geopoint_convert=geopoint_convert,
                                  upsert=upsert, 
                                  verbose=verbose, 
                                  dry_run=dry_run)

@cli.command(cls=StdCommand)
@click.option('--doc-ids', default=None, help='whitespace separated document IDs to delete. If provided, file is ignored.')
@click.argument('file', type=click.File('r'), required=False)
def delete(collection: str, doc_ids: Optional[str], file: Optional[click.File], verbose: bool, dry_run: bool):
    if doc_ids:
        id_list = [doc_id.strip() for doc_id in doc_ids.split(' ') if doc_id.strip()]
        delete_documents_in_firestore(collection, id_list, verbose, dry_run)
    elif file:
        input_format = detect_file_format(file)
        doc_ids = process_deletion_file(file, input_format)
        delete_documents_in_firestore(collection, doc_ids, verbose, dry_run)
    else:
        raise click.UsageError("You must provide either document IDs or a file.")

@cli.command()
def list():
    """Lists all Firestore collections."""

    collections = list_firestore_collections()
    
    for collection in collections:
        try:
            # The collection name can be accessed via collection.id
            click.echo(collection.id)
        except Exception as e:
            logging.error(f"An error occurred while retrieving collection names: {e}")

if __name__ == '__main__':
    cli()
