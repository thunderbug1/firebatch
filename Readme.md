<a href="https://www.buymeacoffee.com/thinx" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;" ></a>

> :coffee: **Open-source tools thrive on caffeine. If you like this project, please consider supporting it.**

# Firebatch: Advanced Firestore CLI Tool

Firebatch streamlines batch operations on Firestore, offering developers a robust CLI tool for managing Google Firestore databases. It simplifies CRUD operations, supports advanced data type conversions, and facilitates efficient data manipulation directly from your command line.

> :warning: **The usage of Firebatch counts towards your read and write quota, use cautiously with large databases.**

## Key Features

### Read/Download
Fetch documents with customizable query conditions, ordering, and limits. Supports raw mode and Firestore type conversions.

### Write
Batch upload documents with server timestamp support and automatic format detection.

### Update
Perform batch updates with upsert functionality and optional data validation.

### Delete
Bulk delete documents, with support for recursive subcollection deletion.

### Validation
Validate documents against custom Pydantic models before writing or updating.

### Verbose and Dry Run Modes
Enable detailed operation logs and simulate write operations without database changes.

### Flexible Input Formats
Supports JSON, JSONL, and auto-detects input data formats.

### Timestamp and Geopoint Conversion
Automatically converts Python datetime and geopoint data to Firestore's Timestamp and GeoPoint types.

### Collection Group Queries
Query across all collections with the same name, regardless of their database location.

### List Collections
Quickly list all top-level collections in your Firestore database.

---

## Installation

> :warning: **Ensure you have Python 3.6 or newer installed before proceeding.**

Install Firebatch using pip:

```sh
pip install firebatch
# For additional validation support:
pip install firebatch[validation]
```
## Examples

### Workflow 1: Geotagging User Posts

Suppose you want to add location data to user posts that lack this information. You can use Firebatch to read, update, and validate geopoint data in bulk.

1. **Export posts lacking geotags** to a JSONL file for review:
   ```sh
   firebatch read --collection posts --where "location == null" --format jsonl > posts_without_geotags.jsonl
   ```
2. **Manually add geotags** to the posts in `posts_without_geotags.jsonl` using your preferred text editor or a script.
3. **Validate and update posts** with geopoint conversion enabled to ensure data integrity:
   ```sh
   firebatch update --collection posts --geopoint-convert --validator my_validators:PostValidator --verbose updates_with_geotags.jsonl
   ```

### Workflow 2: Archiving Old Orders

For orders older than a year, you might want to move them to an archive collection to keep your active orders collection lean and performant.

1. **Identify and export old orders** using timestamp conversion to detect dates properly:
   ```sh
   firebatch read --collection orders --where "date < 2023-01-01" --timestamp-convert --format jsonl --verbose > old_orders.jsonl
   ```
2. **Review the exported data** to ensure accuracy.
3. **Import old orders into the archive** with automatic timestamp updates:
   ```sh
   firebatch write --collection archived_orders --timestamp-field archived_at --timestamp-convert --format jsonl --verbose < old_orders.jsonl
   ```
4. **Delete the original old orders** after confirming the archive's integrity (use dry-run mode first for safety):
   ```sh
   firebatch delete --collection orders --verbose --dry-run old_orders.jsonl
   ```
   After verification, remove `--dry-run` to proceed with deletion.

### Workflow 3: Consolidating User Feedback

Imagine you have feedback stored in multiple collections (e.g., `feedback_2023`, `feedback_2024`) and you want to consolidate all feedback into a single collection for easier analysis.

1. **Perform collection group queries** to fetch all feedback documents:
   ```sh
   firebatch read --collection feedback --collection-group --format jsonl --verbose > all_feedback.jsonl
   ```
2. **Optionally process the feedback data** to fit the new unified format.
3. **Batch upload the consolidated feedback** to a new `unified_feedback` collection:
   ```sh
   firebatch write --collection unified_feedback --format jsonl --verbose all_feedback.jsonl
   ```

---

## Contributing

> :heart: **Your contributions make Firebatch better.**

Report bugs, suggest enhancements, or submit pull requests on our GitHub repository. Join our community to make Firestore more accessible and efficient for developers worldwide.
