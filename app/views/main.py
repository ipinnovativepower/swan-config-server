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
    db, 
    UPLOAD_SERVER, 
    get_all_items_messages_collection,
    add_item_message_collection, 
    set_item_session_collection,
    update_item_session_collection,
    delete_item_session_collection,
    get_item_session_collection,
    set_item_swan_devices_collection,
    update_item_swan_devices_collection,
    delete_item_swan_devices_collection,
    get_item_swan_devices_collection,
    set_item_command_to_swan_collection,
    update_item_command_to_swan_collection,
    delete_item_command_to_swan_collection,
    get_item_command_to_swan_collection,
    update_item_message_collection,
    set_item_message_collection
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


def log_request_details(req):
    logging.info(f"Request method: {req.method}")
    logging.info(f"Request headers:\n{req.headers}")


def fetch_swan_messages():
    """
    Fetch all messages from the 'messages' collection.

    Retrieves all documents in the 'messages' collection, converts them to 
    dictionaries, and returns them as a list.

    Returns:
        list: A list of dictionaries, where each dictionary represents a document 
        from the 'messages' collection.
    """
    results = get_all_items_messages_collection()
    data_list = [doc.to_dict() for doc in results]
    return data_list


def handle_post_request(request):
    """
    Handle POST requests with JSON or CSV content.

    Processes incoming POST requests based on the 'Content-Type' header. 
    Supports both 'application/json' and 'text/csv'. Adds the received data 
    to the 'messages' collection.

    Args:
        request (flask.Request): The incoming request object.

    Returns:
        flask.Response: A JSON response indicating success or failure of 
        the operation, along with the appropriate HTTP status code.
    """
    content_type = request.headers.get("Content-Type")

    if content_type == "application/json":
        # Handle JSON data
        data = request.get_json()
        add_item_message_collection(data)
        return jsonify({"message": "JSON Data added successfully!"}), 201

    elif content_type == "text/csv":
        # Handle CSV data
        csv_string = request.data.decode("utf-8")
        add_item_message_collection({"csv_data": csv_string})
        return jsonify({"message": "CSV Data added successfully!"}), 201

    else:
        return jsonify({"error": "Unsupported Content-Type"}), 400


def handle_post_csv_type(imei):
    """
    Handle POST requests with CSV content from SWAN devices.

    Creates a new session for the SWAN device identified by the given IMEI,
    sets the initial status, and returns a command to retrieve configuration.

    Args:
        imei (str): The IMEI identifier for the SWAN device.

    Returns:
        flask.Response: A JSON response containing the command to retrieve 
        configuration, along with a 200 HTTP status code.
    """
    session_id = f"session_{imei}_{str(uuid.uuid4())[:6]}"
    session_data = {"session_id": session_id, "status": swan_session_steps["0"]}
    set_item_session_collection(session_id, session_data)
    
    command = {
        "cmd": {"type": "get_cfg", "id": session_id}
    }

    update_item_session_collection(session_id, {"status": swan_session_steps["1"]})
    
    return jsonify(command), 200


def send_back_to_upload_server(session_id):
    """
    Send a configuration command back to the upload server.

    Updates the session status to indicate the session is complete and 
    prepares a command to send the configuration data back to the upload server.

    Args:
        session_id (str): The unique identifier for the session.

    Returns:
        flask.Response: A JSON response containing the command to set the 
        configuration, along with a 200 HTTP status code.
    """
    update_item_session_collection(session_id, {"status": swan_session_steps["5"]})
    content = {"upload_server": UPLOAD_SERVER}
    command = {
        "cmd": {
            "type": "set_cfg", 
            "id": session_id,
            "content": format_configuration_string(content)
        }
    }
    
    add_item_message_collection({"session_id": session_id, "description": "Sent SET_CFG command", "content": command})
    return jsonify(command), 200


def send_configuration_to_swan(configuration_elements, session_id, imei):
    """
    Send configuration data to a SWAN device.

    Prepares and sends a 'set_cfg' command with the given configuration elements 
    to the SWAN device identified by the IMEI. Updates session status and logs the action.

    Args:
        configuration_elements (dict): The configuration data to be sent.
        session_id (str): The unique identifier for the session.
        imei (str): The IMEI identifier for the SWAN device.

    Returns:
        flask.Response: A JSON response containing the command to set the 
        configuration, along with a 200 HTTP status code.
    """
    command = {
        "cmd": {
            "type": "set_cfg", 
            "id": session_id,
            "content": format_configuration_string(configuration_elements)
        }
    }
    
    update_item_session_collection(session_id, {"status": swan_session_steps["3"]})
    delete_item_command_to_swan_collection(imei)
    
    document_id = f"{session_id}_{int(time.time())}"
    set_item_message_collection(document_id, {"session_id": document_id, "description": "Sent SET_CFG command", "content": command})
                        
    return jsonify(command), 200


@main_bp.route("/index", methods=["GET"])
def index():
    return render_template("index.html")


@main_bp.route("/swan", methods=["GET", "POST"])
def handle_request():
    """
    Handle GET and POST requests for the SWAN endpoint.

    This function manages requests made to the `/swan` route, which can be 
    either GET or POST. The function performs different operations based on 
    the request method:

    - **GET**: Fetches all messages related to SWAN devices, logs the request,
      and returns the data as a JSON response with a 200 OK status.
    
    - **POST**: Handles data sent from SWAN devices or other clients, either 
      in JSON or CSV format. Depending on the content type and other headers,
      the function either logs the data, initiates sessions for SWAN devices,
      updates configurations, or sends necessary commands back to the devices.

    Args:
        request (flask.Request): The incoming request object, containing data, 
        headers, and other relevant information.

    Returns:
        flask.Response: A JSON response with the appropriate status code based 
        on the outcome of the request handling:
        
        - **200 OK**: For successful GET requests or successful command 
          processing in POST requests.
        - **201 Created**: For successful data addition in POST requests.
        - **400 Bad Request**: If an unsupported content type is provided or 
          there is an error in setting configuration.
        - **Other status codes**: Based on specific conditions handled within 
          the function.
    """
    if request.method == "GET":
        # Fetch messages from SWAN and log the GET request
        data_list = fetch_swan_messages()
        logging.info(f"Received GET request: {request.path}")

        # Return the fetched data as JSON with a 200 OK status
        return jsonify(data_list), 200

    elif request.method == "POST":
        # Handle the POST request and log it
        resp = handle_post_request(request)

        # Extract headers to check if the request is from a SWAN device
        imei = request.headers.get("Wep-Imei")
        content_type = request.headers.get("Content-Type")

        # If IMEI is not present, return the response
        if not imei:
            return resp

        # Handle CSV content type specifically
        if content_type == "text/csv":
            handle_post_csv_type(imei)
        
        # If content type is not JSON, return the response
        if content_type != "application/json":
            return resp
        
        # Parse the JSON data from the request
        data = request.get_json()
        session_id = data['cmd_res']['id']
        session_doc = get_item_session_collection(session_id)

        # If session document does not exist, log it and handle appropriately
        if not session_doc.exists:
            # It is odd if it doesn't exist. Log it. Think of how to handle it.
            pass
        
        # Handle the response code from the SWAN device
        if data['cmd_res']['res_code'] == 0:
            if data['cmd_res']['type'] == "get_cfg":
                # Decode the base64 content and update the SWAN devices collection
                content = data['cmd_res']['content']
                decoded_content = json.loads(base64.b64decode(content).decode("utf-8"))
                
                set_item_swan_devices_collection(imei, decoded_content)
                
                # Get the command to SWAN collection document
                doc = get_item_command_to_swan_collection(imei)
                
                # Check the session status
                session_status = session_doc.to_dict()["status"]
                if session_status == swan_session_steps["5"]:
                    return jsonify({"message": "Session already completed"}), 200
                
                # If document exists, send configuration to SWAN
                if doc.exists:
                    configuration_elements = doc.to_dict()
                    return send_configuration_to_swan(configuration_elements, session_id, imei)
                else:
                    # If no updates, send back to upload server
                    return send_back_to_upload_server(session_id)
                    
            if data['cmd_res']['type'] == "set_cfg":
                # Prepare a command to get configuration and return it
                command = {
                    "cmd": {
                        "type": "get_cfg", 
                        "id": session_id
                    }
                }
                return jsonify(command), 200
                # Return to Galooli
                
        elif data['cmd_res']['res_code'] == 1:
            # Update session status to indicate an error and return an error response
            session_doc.update({"status": swan_session_steps["6"]})
            return jsonify({"error": "Error setting configuration"}), 400
        
        else:
            # Handle unexpected response codes
            # result doesn't equal 1 or 0 and it is not handled 
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