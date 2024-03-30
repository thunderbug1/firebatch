from google.cloud import firestore
import sys

def initialize_firestore_client():
    """Initializes and returns a Firestore client."""
    try:
        db = firestore.Client()
        return db
    except Exception as e:
        error_message = (
            f"Failed to initialize Firestore client: {str(e)}\n"
            "Please ensure you are authenticated. You can do this by running:\n"
            "'gcloud auth login --no-launch-browser' (if you are not logged in already)\n"
            "and then:\n"
            "'gcloud auth application-default login --no-launch-browser',\n"
            "or by setting the GOOGLE_APPLICATION_CREDENTIALS environment variable.\n"
            "More info: https://cloud.google.com/docs/authentication/application-default-credentials\n"
        )
        sys.stderr.write(error_message)
        sys.exit(1)