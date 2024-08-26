import google.cloud.firestore
from google.cloud import firestore
import os


from dotenv import load_dotenv
import time

# Load .env file
load_dotenv()

UPLOAD_SERVER = os.getenv("UPLOAD_SERVER")


# Determine if the app should connect to the Firestore emulator or production Firestore
if "FIRESTORE_EMULATOR_HOST" in os.environ:
    # Using Firestore emulator
    credentials = google.auth.credentials.AnonymousCredentials()
    db = firestore.Client(
        project=os.environ["FIRESTORE_PROJECT_ID"], credentials=credentials
    )
    print("Connected to Firestore Emulator.")
else:
    # Using Production Firestore
    dbname = os.environ.get("FIRESTORE_DB_NAME")
    print(f"DB Name: {dbname}")
    if dbname:
        db = firestore.Client(database=dbname)
    else:
        db = firestore.Client()
    print("Connected to Production Firestore.")
    
    

    
    
    
    
__all__ = ["db", "UPLOAD_SERVER"]