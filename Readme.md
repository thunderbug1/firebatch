# Firebatch

Firebatch is a command-line interface (CLI) tool designed for batch CRUD (Create, Read, Update, Delete) operations on Firestore collections. It provides extensive support for downloading documents, batch uploading, deleting documents, updating records, and more, with advanced features such as data validation, conversion of Firestore specific types, and handling of subcollections.

## Features

- **Read/Download**: Fetch documents with optional query conditions, ordering, and limits. Supports raw mode and conversion for Firestore timestamps and geopoints.
- **Write**: Batch upload with support for server timestamps, automatic format detection, and conversion for Firestore timestamps and geopoints.
- **Update**: Batch updates with optional upsert functionality. Supports validation using custom Pydantic models.
- **Delete**: Batch delete documents, including recursive deletion of subcollections.
- **Validation**: Optionally validate documents using Pydantic models before writing or updating.
- **Verbose and Dry Run Modes**: Detailed logs and simulation of write operations.
- **Flexible Input Formats**: Supports JSON, JSONL, and automatic format detection.
- **Timestamp and Geopoint Conversion**: Automatically convert timestamps and geopoints to and from Firestore specific types.
- **List Collections**: List all top-level Firestore collections.

## Installation

Ensure Python is installed, then install Firebatch. To include validation features, install with the `validation` option:

```sh
pip install firebatch
# With validation support
pip install firebatch[validation]
```

## Usage

### Reading Documents

```sh
firebatch read --collection users/user_id/orders --format jsonl --where "status == completed" --order-by created_at --limit 10 --verbose
```

This command downloads documents from the specified collection path, applying the query conditions, ordering the results, and limiting the output.

```sh
firebatch read --collection users/user_id/orders --format jsonl --raw --verbose  
 ```

This command downloads documents from the specified collection path in raw mode. When the --raw flag is used, the output JSON will not include the document IDs or any additional metadata, only the document data.

Fetch documents with conditions, ordering, and limit. Supports `--timestamp-convert` and `--geopoint-convert` for converting Firestore types.

### Writing Documents

```sh
firebatch write --collection users/user_id/orders --timestamp-field created_at --format auto --verbose --dry-run < data.jsonl
```

Batch upload documents with server timestamps. The `--format auto` option detects the input format.

### Updating Documents

```sh
firebatch update --collection users/user_id/orders --validator my_validators:MyValidatorClass --timestamp-field updated_at --upsert --verbose --dry-run updates.jsonl
```

Update documents with data validation and timestamp updates. The `--upsert` flag allows inserting missing documents.

### Deleting Documents

```sh
firebatch delete --collection users/user_id/orders --verbose --dry-run
```

Delete documents by IDs or recursively delete all documents in a collection, including subcollections.

### Listing Collections

```sh
firebatch list
```

List all top-level Firestore collections.

## Configuration

To use Firebatch, authenticate with Google Cloud Firestore by logging in or setting up your service account key:

```sh
gcloud auth application-default login --no-launch-browser
# Or
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

Firebatch requires initialization of a Firestore client for operations.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests on the GitHub repository.

---

This updated README provides a comprehensive overview of Firebatch's capabilities, reflecting the enhancements and new features introduced in the code.