from flask import Flask, request, jsonify, Response
import logging
import requests
import google.cloud.firestore
import os

from utils import redirect_to_API_HOST
from swan_commands import SET_CFG


app = Flask(__name__)
dbname = os.environ['FIRESTORE_DB_NAME']
db = google.cloud.firestore.Client(database=dbname)  # Initialize Firestore client


# Configure logging to file
logging.basicConfig(filename='server.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Create a handler for logging to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

# Add the console handler to the root logger
logging.getLogger().addHandler(console_handler)


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello, World!'

@app.route('/command', methods=['GET'])
def command():
    imei = request.args.get('imei')
    command = request.args.get('command')
    
    data = {
        'imei': imei,
        'command': command
    }
    
    db.collection('commands').add(data)
    return jsonify({'message': 'Command added successfully!'}), 201


@app.route('/swan', methods=['GET', 'POST'])
def handle_request():
    if request.method == 'GET':
        results = db.collection('messages').stream()
        data_list = [doc.to_dict() for doc in results]

        logging.info(f'Received GET request: {request.path}')
        # log_request_details(request)
        return jsonify(data_list), 200

    elif request.method == 'POST':
        imei = request.headers.get('Wep-Imei')

        if imei:
           results = db.collection('commands').stream()
           
           for doc in results:
                doc_data = doc.to_dict()
                if doc_data['imei'] == imei:
                    if doc_data['command'] == 'set_cfg':
                        command = SET_CFG
                    else:
                        command = {
                            "cmd": {
                                "type": "get_cfg",
                                "id": "0123456789"
                                }
                            }
                    
                    db.collection('commands').document(doc.id).delete()
                    return jsonify(command), 200
                   
        resp = handle_post_request(request)
        return resp
                    

def handle_post_request(request):
    content_type = request.headers.get('Content-Type')
    
    if content_type == 'application/json':
            # Handle JSON data
            data = request.get_json()
            db.collection('messages').add(data)
            return jsonify({'message': 'JSON Data added successfully!'}), 201

    elif content_type == 'text/csv':
        # Handle CSV data
        csv_string = request.data.decode('utf-8')
        db.collection('messages').add({'csv_data': csv_string})

        return jsonify({'message': 'CSV Data added successfully!'}), 201

    else:
        return jsonify({'error': 'Unsupported Content-Type'}), 400




def log_request_details(req):
    logging.info(f'Request method: {req.method}')
    logging.info(f'Request headers:\n{req.headers}')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
