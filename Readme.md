# Firebatch

Firebatch is a powerful and versatile command-line interface (CLI) tool designed for batch CRUD (Create, Read, Update, Delete) operations on Firestore collections. It supports various operations like downloading documents, writing to collections, deleting documents, and updating existing records in batch modes.

## Features

- **Read/Download**: Fetch documents from a Firestore collection with optional query conditions, ordering, and limits.
- **Write**: Batch upload documents to a Firestore collection, with support for server timestamps.
- **Update**: Perform batch updates on documents in a Firestore collection with optional upsert functionality.
- **Delete**: Batch delete documents by document IDs from a Firestore collection.
- **Validation**: Validate documents using custom Pydantic models before writing or updating.
- **Verbose and Dry Run Modes**: Provide detailed logs of operations and allow simulation of write operations without affecting the database.
- **Flexible Input Formats**: Accept data in both JSON and JSONL formats for batch operations.
- **Raw Mode**: Retrieve or write documents without wrapping them in metadata such as document IDs, providing raw document data.

## Installation

Before you can use Firebatch, ensure you have Python installed on your machine and then install it using pip:

```sh
pip install firebatch
```

## Usage

Below are examples of how to use Firebatch for different operations:

### Reading Documents

```sh
firebatch read --collection users/user_id/orders --format jsonl --where "status == completed" --order-by created_at --limit 10 --verbose
```

This command downloads documents from the specified collection path, applying the query conditions, ordering the results, and limiting the output.

```sh
firebatch read --collection users/user_id/orders --format jsonl --raw --verbose  
 ```

This command downloads documents from the specified collection path in raw mode. When the --raw flag is used, the output JSON will not include the document IDs or any additional metadata, only the document data.

### Writing Documents

```sh
firebatch write --collection users/user_id/orders --timestamp-field created_at --format jsonl --verbose --dry-run < data.jsonl
```

This command uploads documents to the specified collection. The `--timestamp-field` option adds a server timestamp to the specified field. The `--dry-run` flag simulates the write operation without committing changes to the database.

### Updating Documents

```sh
firebatch update --collection users/user_id/orders --validator my_validators:MyValidatorClass --timestamp-field updated_at --upsert --verbose --dry-run updates.jsonl
```

This command updates documents in the specified collection with the provided updates. It can validate the data using a Pydantic model and update the timestamp field. The `--upsert` flag allows inserting documents if they do not exist.

### Deleting Documents

```sh
firebatch delete --collection users/user_id/orders --doc-ids "doc1 doc2 doc3" --verbose --dry-run
```

This command deletes documents with the specified IDs from the collection. If a file with document IDs is provided instead of `--doc-ids`, it will process the file and delete the corresponding documents.

## Configuration

To use Firebatch, you'll need to authenticate with Google Cloud Firestore. Either login with:

```sh
gcloud auth application-default login --no-launch-browser
```

or set up your Google Cloud credentials by exporting the path to your service account key:

```sh
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

Alternatively, if running in a Google Cloud environment, Firebatch will use the default service account

## Contributing
 
Contributions to Firebatch are welcome! Please feel free to open issues or submit pull requests on the GitHub repository.