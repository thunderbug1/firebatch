import pytest
from google.cloud import firestore
from firebatch.operations import download_collection_documents, write_documents, delete_documents_in_firestore, update_documents_in_firestore
from io import StringIO
import json

@pytest.fixture(scope='module')
def db_client():
    # Initialize and return a Firestore client
    return firestore.Client()

@pytest.fixture(scope='module')
def setup_test_environment(db_client):
    # Set up test collection and documents, yield them for testing, and clean up afterwards
    test_collection = 'test_collection'
    test_documents = [{'name': 'Test Name 1', 'value': 10}, {'name': 'Test Name 2', 'value': 20}]
    # Insert test documents
    for doc in test_documents:
        db_client.collection(test_collection).add(doc)
    yield test_collection, test_documents
    # Clean up: delete all documents from the test collection
    batch = db_client.batch()
    docs = db_client.collection(test_collection).stream()
    for doc in docs:
        batch.delete(doc.reference)
    batch.commit()

def test_download_collection_documents(db_client, setup_test_environment):
    test_collection, _ = setup_test_environment
    downloaded_docs = download_collection_documents(test_collection, 'json', verbose=True)
    downloaded_docs = json.loads(downloaded_docs)
    assert len(downloaded_docs) > 0  # Replace with actual length of your test documents if fixed

def test_write_documents(db_client, setup_test_environment):
    test_collection, test_documents = setup_test_environment
    # Convert test_documents to StringIO for upload
    upload_data = StringIO(json.dumps(test_documents))
    write_documents(test_collection, upload_data, format="json", verbose=True, dry_run=False)
    # Verify documents are written
    docs = list(db_client.collection(test_collection).stream())
    assert len(docs) == len(test_documents*2) # test docs are written in fixture and here

def test_update_documents_in_firestore(db_client, setup_test_environment):
    test_collection, _ = setup_test_environment
    docs = json.loads(download_collection_documents(test_collection, 'json', verbose=True))
    updates = {'name': 'Updated Name', 'value': 15}
    docs[0]['__data__'] = updates
    update_documents_in_firestore(test_collection, docs, verbose=True, dry_run=False)
    updated_docs = json.loads(download_collection_documents(test_collection, 'json', verbose=True))
    # Verify updates
    assert updated_docs[0]['__data__'] == updates

def test_delete_documents_in_firestore(db_client, setup_test_environment):
    test_collection, test_documents = setup_test_environment
    docs = json.loads(download_collection_documents(test_collection, 'json', verbose=True))
    doc_ids_to_delete = [docs[0]['__doc_id__']]
    delete_documents_in_firestore(test_collection, doc_ids_to_delete, verbose=True, dry_run=False)
    # Verify deletion
    updated_docs = json.loads(download_collection_documents(test_collection, 'json', verbose=True))
    print(updated_docs)
    assert [updated_docs[0]['__doc_id__']] != doc_ids_to_delete
