from flask import Flask, request, jsonify, Response, Blueprint, flash
from flask import render_template
import logging
import requests
import google.cloud.firestore
from google.cloud import firestore
import os

from utils import redirect_to_API_HOST
from swan_commands import SET_CFG
from app.forms import ImeiForm
from dotenv import load_dotenv


main_bp = Blueprint("main", __name__)


# Load .env file
load_dotenv()


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
    if dbname:
        db = firestore.Client(database=dbname)
    else:
        db = firestore.Client()
    print("Connected to Production Firestore.")


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


@main_bp.route("/swan", methods=["GET", "POST"])
def handle_request():
    if request.method == "GET":
        results = db.collection("messages").stream()
        data_list = [doc.to_dict() for doc in results]

        logging.info(f"Received GET request: {request.path}")
        # log_request_details(request)
        return jsonify(data_list), 200

    elif request.method == "POST":
        # Only logging
        resp = handle_post_request(request)

        # Checking if the request is coming from the SWAN device
        imei = request.headers.get("Wep-Imei")
        content_type = request.headers.get("Content-Type")

        if imei:       
            
            results = db.collection("commands").stream()

            for doc in results:
                doc_data = doc.to_dict()
                if doc_data["imei"] == imei:
                    if doc_data["command"] == "set_cfg":
                        command = {
                            "cmd": {
                                "type": "set_cfg",
                                "id": "0123456789",
                                "content": '{"device_tag":"Changed Tag", "collect_mode":8}',
                            }
                        }
                    else:
                        command = {
                            "cmd": {"type": "get_cfg", "id": doc_data["command_id"]}
                        }

                    db.collection("commands").document(doc.id).delete()
                    return jsonify(command), 200

        return resp


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
    data = {
        "imei": imei,
        "device_tag": "",
        "nb1_plmn": "",
        "nb1_bands": "3,8,20",
        "nb1_apn": "",
        "nb1_psm": 0,
        "nb1_psm_activetime": 0,
        "nb1_psm_tau": 0,
        "nb1_rai": 3,
        "nb1_apn_account_index": 0,
        "ntp_server": "0.europe.pool.ntp.org",
        "ntp_port": 123,
        "ntp_auto_sync": 0,
        "timezone": 4,
        "daylightsaving_enable": 1,
        "upload_server": "weptech-iot.de/swan2",
        "upload_remote_port": 31031,
        "upload_local_port": 28028,
        "upload_proto": 3,
        "upload_method": 1,
        "upload_account_index": 0,
        "upload_format": 2,
        "upload_format_spec_1": 0xFFFFFFFF,
        "upload_format_spec_2": 0xFFFFFFFF,
        "upload_format_spec_3": 0xFFFFFFFF,
        "upload_retries": 2,
        "upload_months": 4095,
        "upload_days": 16385,
        "upload_weeks": 0,
        "upload_week_days": 0,
        "upload_start_hour": 0,
        "upload_start_minute": 0,
        "upload_hours": 0,
        "upload_per_hour": 1,
        "upload_jitter": 0,
        "lwm2m_idle_time": 120,
        "lwm2m_notify_with_ack": 1,
        "lwm2m_notify_retry_cnt": 2,
        "lwm2m_notify_timeout": 7,
        "lwm2m_lifetime": 150,
        "collect_mode": 8,
        "collect_rssi_min": -108,
        "collect_rssi_max": 127,
        "collect_use_dll": 0,
        "collect_max_num_meters": 5,
        "collect_duration": 300,
        "collect_flags": 0,
        "collect_datalog_flags": 3,
        "collect_months": 4095,
        "collect_days": 16385,
        "collect_weeks": 0,
        "collect_week_days": 0,
        "collect_start_hour": 0,
        "collect_start_minute": 0,
        "collect_hours": 0,
        "collect_per_hour": 1,
        "collect_jitter": 0,
        "upload_after_collect": 0,
        "collect_mode_2": 0,
        "collect_rssi_min_2": -108,
        "collect_rssi_max_2": 127,
        "collect_use_dll_2": 0,
        "collect_max_num_meters_2": 5,
        "collect_duration_2": 300,
        "collect_flags_2": 0,
        "collect_datalog_flags_2": 3,
        "collect_months_2": 0,
        "collect_days_2": 0,
        "collect_weeks_2": 0,
        "collect_week_days_2": 0,
        "collect_start_hour_2": 0,
        "collect_start_minute_2": 0,
        "collect_hours_2": 0,
        "collect_per_hour_2": 1,
        "collect_jitter_2": 0,
        "upload_after_collect_2": 0,
        "quietmode": 0,
        "nfc_fast_install": 1,
        "uart_sci": 0,
        "ci_field_blacklist": 0,
        "autostart": 0,
        "clear_status_after_ul": 1,
        "prefilter_devicetype": "",
        "prefilter_manufacturer": "",
        "sync_rx": 1,
        "sync_rx_duration": 2000,
        "sync_rx_interval": 300,
        "sync_rx_storage": 3600,
        "sync_rx_max_time_gap": 3600,
        "sync_rx_meter": "12345678-WEP-02-02",
        "upload_alarm_mask": 0,
        "upload_alarm_interval": 80,
    }

    db.collection("swan_devices").document(imei).set(data)
    return jsonify({"message": "Swan device added successfully!"}), 201


@main_bp.route("/add/command_to_swan/<imei>", methods=["POST"])
def update_swan(imei):
    data = request.get_json()
    doc_ref = db.collection("command_to_swan").document(f"update-{imei}")

    if doc_ref.get().exists:
        doc_ref.update(data)
        return jsonify({"message": "Swan device updated successfully!"}), 200
    else:
        doc_ref.set(data)
        return jsonify({"message": "Swan device created successfully!"}), 201


@main_bp.route("/delete/swan/<imei>", methods=["DELETE"])
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
