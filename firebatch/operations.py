import json
import sys
from typing import Any, Dict, List, Optional, TextIO, Tuple
from tqdm import tqdm

from firebatch.endcoding import convert_to_firestore_types, to_json
from firebatch.utils import get_nested_collection_reference, read_documents
from firebatch.firestore_client import initialize_firestore_client
from google.api_core.exceptions import NotFound
from google.cloud.firestore import SERVER_TIMESTAMP
import logging
logger = logging.getLogger(__name__)

def print_verbose(message: str, verbose: bool):
    """Prints message if verbose mode is enabled."""
    if verbose:
        logger.info(message)

def download_collection_documents(collection_path: str, 
                                  output_format: str = 'jsonl', 
                                  timestamp_convert: bool = False, 
                                  geopoint_convert: bool = False,
                                  raw : bool = False, 
                                  conditions: List[Tuple[str, str, Any]] = [], 
                                  order_by: Optional[str] = None, 
                                  limit: Optional[int] = None, 
                                  verbose: bool = False):

    db = initialize_firestore_client()
    query_ref = get_nested_collection_reference(db, collection_path)
    
    for field, operator, value in conditions:
        logger.debug(f"apply conditions: {conditions}")
        if value.lower() == "null" or value.lower() == "none":
            value = None
        query_ref = query_ref.where(field, operator, value)

    if order_by:
        query_ref = query_ref.order_by(order_by)
    if limit:
        query_ref = query_ref.limit(limit)

    if raw:
        documents = [doc.to_dict() for doc in tqdm(query_ref.stream(), desc="Downloading documents", disable=not verbose)]
    else:
        documents = [{"__doc_id__": doc.id, "__data__": doc.to_dict()} for doc in tqdm(query_ref.stream(), desc="Downloading documents", disable=not verbose)]

    print_verbose(f"Retrieved {len(documents)} documents from '{collection_path}'.", verbose)
    
    if output_format == 'json':
        return to_json(documents, 2, timestamp_convert, geopoint_convert)
    elif output_format == 'jsonl':
        return '\n'.join(to_json(doc, None, timestamp_convert, geopoint_convert) for doc in documents)  # One JSON document per line

def write_documents(collection_path: str, 
                    file: TextIO, 
                    timestamp_field: str = None, 
                    timestamp_convert: bool = False, 
                    geopoint_convert: bool = False,
                    format: str="auto",
                    verbose: bool = False, 
                    dry_run: bool = False):
    db = initialize_firestore_client()
    collection_ref = get_nested_collection_reference(db, collection_path)
    batch = db.batch()

    documents = read_documents(file)
    total_documents = len(documents)

    with tqdm(total=total_documents, desc=f"Uploading documents to {collection_path}", disable=not verbose) as pbar:
        for data in documents:
            if "__doc_id__" in data and "__data__" in data:
                doc_id = data["__doc_id__"]
                data = convert_to_firestore_types(db, data["__data__"], timestamp_convert, geopoint_convert)
            else:
                doc_id = None
                data = convert_to_firestore_types(db, data, timestamp_convert, geopoint_convert)
            if timestamp_field:
                data[timestamp_field] = SERVER_TIMESTAMP
            doc_ref = collection_ref.document(doc_id)  # Auto-generate document ID if None
            batch.set(doc_ref, data)

            pbar.update(1)

            # Commit in batches to avoid exceeding Firestore batch size limits
            if pbar.n % 500 == 0 and not dry_run:
                batch.commit()
                batch = db.batch()  # Start a new batch after committing

        if not dry_run and total_documents > 0:
            batch.commit()  # Commit any remaining documents in the batch

    print_verbose(f"Uploaded {total_documents} documents to '{collection_path}'.", verbose)

def delete_collection_recursive(collection_ref, batch_size=10):
    """Delete all documents within a collection, including documents in subcollections."""
    while True:
        # Retrieve a small batch of documents to avoid consuming too much memory
        docs = collection_ref.limit(batch_size).stream()
        deleted = 0

        for doc in docs:
            # Recursively delete subcollections
            for subcollection in doc.reference.collections():
                delete_collection_recursive(subcollection, batch_size=batch_size)

            doc.reference.delete()  # Delete the document itself
            deleted += 1

        if deleted == 0:
            break  # All documents have been deleted

def delete_documents_in_firestore(collection_path: str, doc_ids: List[str], verbose: bool = False, dry_run: bool = False):
    db = initialize_firestore_client()
    collection_ref = get_nested_collection_reference(db, collection_path)

    with tqdm(total=len(doc_ids), disable=not verbose, desc="Deleting documents") as pbar:
        for doc_id in doc_ids:
            doc_ref = collection_ref.document(doc_id)

            # First, delete subcollections recursively
            if not dry_run:
                for subcollection in doc_ref.collections():
                    delete_collection_recursive(subcollection)

                # Then delete the document itself
                doc_ref.delete()

            if verbose:
                print(f"Deleted document with ID '{doc_id}' from '{collection_path}', including its subcollections.")
            pbar.update(1)

def process_deletion_file(documents) -> List[str]:
    try:
        doc_ids = [doc["__doc_id__"] for doc in documents if "__doc_id__" in doc]
    except KeyError as _:
        raise ValueError("document does not contain document ids, please export the documents without the '--raw' option.")
    if not doc_ids:
        raise ValueError("No document IDs found in the file.")
    return doc_ids


def update_documents_in_firestore(collection_path: str, 
                                  updates: List[dict], 
                                  timestamp_field: Optional[str] = None, 
                                  timestamp_convert: bool = False, 
                                  geopoint_convert: bool = False,
                                  upsert: bool = False,
                                  verbose: bool = False, 
                                  dry_run: bool = False):
    db = initialize_firestore_client()
    batch = db.batch()
    collection_ref = get_nested_collection_reference(db, collection_path)

    # First, check for duplicate keys in the updates
    seen_doc_ids = set()
    duplicates = set()
    for update in updates:
        doc_id = update.get("__doc_id__")
        if doc_id:
            if doc_id in seen_doc_ids:
                duplicates.add(doc_id)
            else:
                seen_doc_ids.add(doc_id)

    if duplicates:
        sys.stderr.write(f"Error duplicate keys: {duplicates}")
        sys.exit(1)

    try:

        with tqdm(total=len(updates), desc="Updating documents", disable=not verbose) as pbar:
            for update in updates:
                doc_id = update.get("__doc_id__")
                data = update.get("__data__")
                if not doc_id or not data:
                    continue  # Skip if no document ID or data

                data = convert_to_firestore_types(db, data, timestamp_convert, geopoint_convert) 

                if timestamp_field:
                    data[timestamp_field] = SERVER_TIMESTAMP

                doc_ref = collection_ref.document(doc_id)
                if upsert:
                    batch.set(doc_ref, data, merge=True) 
                else:
                    batch.update(doc_ref, data)

                if pbar.n % 500 == 0 and not dry_run:  # Firestore batch limit
                    batch.commit()
                    batch = db.batch()  # Start a new batch after committing
                
                pbar.update(1)

            if not dry_run and pbar.n % 500 != 0:  # Commit any remaining documents
                batch.commit()

            if verbose:
                logging.info(f"Batch updated {pbar.n} documents in '{collection_path}'.")
    except NotFound as ex:
        raise Exception(f"{str(ex)} ... you can resolve this by using the --upsert flag to insert missing keys.")

def list_firestore_collections():
    db = initialize_firestore_client()  # Make sure this function returns a Firestore client instance.
    collections = db.collections()
    return collections