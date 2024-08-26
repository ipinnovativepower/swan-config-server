from flask import request, jsonify, Blueprint
from flask import render_template
import logging
import google.cloud.firestore
from google.cloud import firestore
import os
import uuid
import json
import base64

from dotenv import load_dotenv
import time

from app.config import SWAN_DEFAULT_CONFIG
from app.utils.db_utils import (
    db
)

main_bp = Blueprint("main", __name__)

swan_session_steps = {
    "0": "created",
    "1": "sent get_cfg",
    "2": "received get_cfg",
    "3": "sent set_cfg",
    "4": "received set_cfg",
    "5": "returned to Galooli",
    "6": "error"
}


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


def json_to_string(json_obj):
    # Convert the JSON object to a string
    json_str = json.dumps(json_obj)
    
    # Escape the double quotes in the string
    formatted_str = json_str.replace('"', r'\"')
    
    # Add the outer double quotes
    formatted_str = f'"{formatted_str}"'
    
    return formatted_str

def format_configuration_string(dict):
    format_configuration_string = ""
    for key, value in dict.items():
        if type(value) == str:
            format_configuration_string += f"\"{key}\":\"{value}\","
        else:
            format_configuration_string += f"\"{key}\":{value}"
        
    return (f"\u007b{format_configuration_string[:-1]}\u007d")


# Configure logging to file
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a handler for logging to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

# Add the console handler to the root logger
logging.getLogger().addHandler(console_handler)


@main_bp.route("/", methods=["GET"])
def hello_world():
    return "Hello, World!"


@main_bp.route("/index", methods=["GET"])
def index():
    return render_template("index.html")


@main_bp.route("/command", methods=["GET"])
def command():
    imei = request.args.get("imei")
    command = request.args.get("command")
    command_id = request.args.get("command_id", "0123456789")

    data = {"imei": imei, "command": command, "command_id": command_id}

    db.collection("commands").add(data)
    return jsonify({"message": "Command added successfully!"}), 201


def fetch_swan_messages():
    results = db.collection("messages").stream()
    data_list = [doc.to_dict() for doc in results]
    return data_list

def handle_post_request(request):
    content_type = request.headers.get("Content-Type")

    if content_type == "application/json":
        # Handle JSON data
        data = request.get_json()
        db.collection("messages").add(data)
        return jsonify({"message": "JSON Data added successfully!"}), 201

    elif content_type == "text/csv":
        # Handle CSV data
        csv_string = request.data.decode("utf-8")
        db.collection("messages").add({"csv_data": csv_string})

        return jsonify({"message": "CSV Data added successfully!"}), 201

    else:
        return jsonify({"error": "Unsupported Content-Type"}), 400


@main_bp.route("/swan", methods=["GET", "POST"])
def handle_request():
    if request.method == "GET":
        data_list = fetch_swan_messages()
        logging.info(f"Received GET request: {request.path}")

        return jsonify(data_list), 200

    elif request.method == "POST":
        # Only logging
        resp = handle_post_request(request)

        # Checking if the request is coming from the SWAN device
        imei = request.headers.get("Wep-Imei")
        content_type = request.headers.get("Content-Type")

        if not imei:
            return resp

        if content_type == "text/csv":
            session_id = f"session_{imei}_{str(uuid.uuid4())[:6]}"
            session_data = {"session_id": session_id, "status": swan_session_steps["0"]}
            db.collection("sessions").document(session_id).set(session_data)
            
            command = {
                "cmd": {"type": "get_cfg", "id": session_id}
            }

            db.collection("sessions").document(session_id).update({"status": swan_session_steps["1"]})
            
            return jsonify(command), 200

        if content_type != "application/json":
            return resp
            
        data = request.get_json()
        session_id = data['cmd_res']['id']
        session_doc = db.collection("sessions").document(session_id).get()

        if not session_doc.exists:
            # It is odd if it doesn't exist. Log it. Think of how to handle it.
            pass
        
        
        if data['cmd_res']['res_code'] == 0:
            if data['cmd_res']['type'] == "get_cfg":
                # Check for awaiting updates
                # If there are updates, send them
                # If there are no updates, return to Galooli
                content = data['cmd_res']['content']
                decoded_content = json.loads(base64.b64decode(content).decode("utf-8"))
                
                db.collection("swan_devices").document(imei).set(decoded_content)
                
                
                doc = db.collection("command_to_swan").document(f"update-{imei}").get()
                
                session_status = session_doc.to_dict()["status"]
                if session_status == swan_session_steps["5"]:
                    return jsonify({"message": "Session already completed"}), 200

                
                if doc.exists:
                    configuration_elements = doc.to_dict()
                    command = {
                        "cmd": {
                            "type": "set_cfg", 
                            "id": session_id,
                            # "content": '''{\"device_tag\":\"Changed Tag\", \"collect_mode\":8}'''
                            "content": format_configuration_string(configuration_elements)
                        }
                    }
                    db.collection("sessions").document(session_id).update({"status": swan_session_steps["3"]})
                    db.collection("command_to_swan").document(f"update-{imei}").delete()
                    document_id = f"{session_id}_{int(time.time())}"
                    db.collection("messages").document(document_id).set({"session_id": document_id, "description": "Sent SET_CFG command", "content": command})

                    return jsonify(command), 200
                else:
                    db.collection("sessions").document(session_id).update({"status": swan_session_steps["5"]})
                    content = {"upload_server": UPLOAD_SERVER}
                    command = {
                        "cmd": {
                            "type": "set_cfg", 
                            "id": session_id,
                            "content": format_configuration_string(content)
                        }
                    }
                    
                    db.collection("messages").add({"session_id": session_id, "description": "Sent SET_CFG command", "content": command})
                    return jsonify(command), 200
                

                
            if data['cmd_res']['type'] == "set_cfg":
                # db.collection("sessions").document(session_id).update({"status": swan_session_steps["1"]})
                command = {
                    "cmd": {
                        "type": "get_cfg", 
                        "id": session_id
                    }
                }
                return jsonify(command), 200
                # Return to Galooli
                
        elif data['cmd_res']['res_code'] == 1:
            if data['cmd_res']['type'] == "get_cfg":
                session_doc.update({"status": swan_session_steps["6"]})
                # Handle error
                return jsonify({"error": "Error setting configuration"}), 400

            if data['cmd_res']['type'] == "set_cfg":
                session_doc.update({"status": swan_session_steps["6"]})
                # Handle error
                return jsonify({"error": "Error setting configuration"}), 400        
        
        else:
            # reult doesn't equal 1 or 0 and it is not handled 
            pass
        


# Can be moved to API blueprint
@main_bp.route("/get_swan_devices", methods=["GET"])
def get_swan_devices():
    devices = db.collection("swan_devices").stream()
    device_list = [{device.id: device.to_dict()} for device in devices]
    return jsonify(device_list), 200


@main_bp.route("/get_swan_device/<imei>", methods=["GET"])
def get_swan_device(imei):
    device_ref = db.collection("swan_devices").document(imei)
    device = device_ref.get()
    if device.exists:
        return jsonify({"device_details": device.to_dict()}), 200
    else:
        return jsonify({"error": "Device not found"}), 404


@main_bp.route("/get_command_to_swan", methods=["GET"])
def get_command_to_swan():
    commands = db.collection("command_to_swan").stream()
    command_list = [{command.id: command.to_dict()} for command in commands]
    return jsonify(command_list), 200


@main_bp.route("/get_sessions", methods=["GET"])
def get_sessions():
    commands = db.collection("sessions").stream()
    command_list = [{command.id: command.to_dict()} for command in commands]
    return jsonify(command_list), 200


@main_bp.route("/add/swan/<imei>", methods=["GET"])
def add_swan(imei):
    data = SWAN_DEFAULT_CONFIG

    db.collection("swan_devices").document(imei).set(data)
    return jsonify({"message": "Swan device added successfully!"}), 201


@main_bp.route("/add/command_to_swan/<imei>", methods=["POST"])
def update_swan(imei):
    data = request.get_json()
    doc_ref = db.collection("command_to_swan").document(f"update-{imei}")

    if doc_ref.get().exists:
        doc_ref.set(data)
        return jsonify({"message": "Swan device updated successfully!"}), 200
    else:
        doc_ref.set(data)
        return jsonify({"message": "Swan device created successfully!"}), 201


@main_bp.route("/delete/swan/<imei>", methods=["GET", "DELETE"])
def delete_swan(imei):
    # Reference to the document with the given IMEI
    doc_ref = db.collection("swan_devices").document(imei)

    # Check if the document exists
    if doc_ref.get().exists:
        # Delete the document
        doc_ref.delete()
        return jsonify({"message": "Swan device deleted successfully!"}), 200
    else:
        return jsonify({"error": "Swan device not found!"}), 404


@main_bp.route("/delete/command_to_swan/<imei>", methods=["GET", "DELETE"])
def delete_command_to_swan(imei):
    # Reference to the document with the given IMEI
    doc_ref = db.collection("command_to_swan").document(f"update-{imei}")

    # Check if the document exists
    if doc_ref.get().exists:
        # Delete the document
        doc_ref.delete()
        return jsonify({"message": "Swan command deleted successfully!"}), 200
    else:
        return jsonify({"error": "Swan command not found!"}), 404


def log_request_details(req):
    logging.info(f"Request method: {req.method}")
    logging.info(f"Request headers:\n{req.headers}")
