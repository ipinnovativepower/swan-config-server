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
    
    
# Messages Collection
def get_all_items_messages_collection():
    docs = db.collection("messages").stream()
    
    return docs

def add_item_message_collection(data):
    db.collection("messages").add(data)
    
    return 1

def set_item_message_collection(message_id, data):
    db.collection("messages").document(message_id).set(data)
    
    return 1

def update_item_message_collection(message_id, data):
    db.collection("messages").document(message_id).update(data)
    
    return 1

# Session Collection
def get_item_session_collection(session_id):
    doc = db.collection("sessions").document(session_id).get()
    
    return doc

def set_item_session_collection(session_id, data):
    db.collection("sessions").document(session_id).set(data)
    
    return 1

def update_item_session_collection(session_id, data):
    db.collection("sessions").document(session_id).update(data)
    
    return 1

def delete_item_session_collection(session_id):
    db.collection("sessions").document(session_id).delete()
    
    return 1

# Swan Devices Collection
def get_item_swan_devices_collection(imei):
    doc = db.collection("swan_devices").document(imei).get()
    
    return doc

def set_item_swan_devices_collection(imei, data):
    db.collection("swan_devices").document(imei).set(data)
    
    return 1

def update_item_swan_devices_collection(imei, data):
    db.collection("swan_devices").document(imei).update(data)
    
    return 1

def delete_item_swan_devices_collection(imei):
    db.collection("swan_devices").document(imei).delete()
    
    return 1
    
# Command To Swan Collection
def get_item_command_to_swan_collection(imei):
    doc = db.collection("command_to_swan").document(f"update-{imei}").get()
    
    return doc

def set_item_command_to_swan_collection(imei, data):
    db.collection("command_to_swan").document(f"update-{imei}").set(data)
    
    return 1

def update_item_command_to_swan_collection(imei, data):
    db.collection("command_to_swan").document(f"update-{imei}").update(data)
    
    return 1

def delete_item_command_to_swan_collection(imei):
    db.collection("command_to_swan").document(f"update-{imei}").delete()
    
    return 1



    
    
__all__ = [
    "db", 
    "UPLOAD_SERVER", 
    "add_item_message_collection", 
    "set_item_session_collection",
    "update_item_session_collection",
    "delete_item_session_collection",
    "get_item_session_collection",
    "set_item_swan_devices_collection",
    "update_item_swan_devices_collection",
    "delete_item_swan_devices_collection",
    "get_item_swan_devices_collection",
    "set_item_command_to_swan_collection",
    "update_item_command_to_swan_collection",
    "delete_item_command_to_swan_collection",
    "get_item_command_to_swan_collection",
    "get_all_items_messages_collection",
    "update_item_message_collection",
    "set_item_message_collection"
]
