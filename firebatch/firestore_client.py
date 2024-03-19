from google.cloud import firestore
import sys

def initialize_firestore_client():
    """Initializes and returns a Firestore client."""
    try:
        db = firestore.Client()
        return db
    except Exception as e:
        print("Failed to initialize Firestore client:", str(e))
        print("Please ensure you are authenticated. You can do this by running 'gcloud auth application-default login --no-launch-browser',")
        print("or by setting the GOOGLE_APPLICATION_CREDENTIALS environment variable.")
        print("More info: https://cloud.google.com/docs/authentication/application-default-credentials")
        sys.exit(1)
