import pytest
from flask import Flask, jsonify, request
from app import create_app  # Adjust the import based on your app structure
from unittest.mock import patch, MagicMock

# This mimcs the action of a SWAN device


@pytest.fixture
def client():
    app = create_app()  # Adjust this based on how you create your Flask app
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_get_swan(client):
    response = client.get("/swan")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_post_swan_csv(client):
    headers = {
        "Wep-Imei": "123111111113",
        "Content-Type": "text/csv"
    }
    response = client.post("/swan", headers=headers)
    assert response.status_code == 200
    assert "cmd" in response.get_json()

@patch('app.views.main.db')
def test_post_swan_json_get_cfg_success(mock_db, client):
    headers = {
        "Wep-Imei": "123111111113",
        "Content-Type": "application/json"
    }
    payload = {
        "cmd_res": {
            "type": "get_cfg",
            "id": "session_123111111113_1",
            "res_code": 0
        }
    }

    # Mock the Firestore document get and update methods
    mock_document = MagicMock()
    mock_document.get.return_value.exists = True
    mock_document.get.return_value.to_dict.return_value = {"key": "value"}  # Return a serializable dictionary
    mock_db.collection.return_value.document.return_value = mock_document

    response = client.post("/swan", headers=headers, json=payload)

    assert response.status_code == 200
    assert "cmd" in response.get_json()
    assert response.get_json()["cmd"]["type"] == "set_cfg"

    # Verify that the document update method was called with the correct arguments
    mock_document.update.assert_called_with({"status": "sent set_cfg"})
    
@patch('app.views.main.db')
def test_post_swan_json_get_cfg_failure(mock_db, client):
    headers = {
        "Wep-Imei": "123111111113",
        "Content-Type": "application/json"
    }
    payload = {
        "cmd_res": {
            "type": "get_cfg",
            "id": "session_123111111113_1",
            "res_code": 1
        }
    }

    # Mock the Firestore document get and update methods
    mock_document = MagicMock()
    mock_document.get.return_value.exists = True
    mock_document.get.return_value.to_dict.return_value = {"key": "value"}  # Return a serializable dictionary
    mock_db.collection.return_value.document.return_value = mock_document

    response = client.post("/swan", headers=headers, json=payload)
    assert response.status_code == 400

@patch('app.views.main.db')
def test_post_swan_json_set_cfg_success(mock_db, client):
    headers = {
        "Wep-Imei": "123111111113",
        "Content-Type": "application/json"
    }
    payload = {
        "cmd_res": {
            "type": "set_cfg",
            "id": "session_123111111113_1",
            "res_code": 0
        }
    }

    # Mock the Firestore document get and update methods
    mock_document = MagicMock()
    mock_document.get.return_value.exists = True
    mock_document.get.return_value.to_dict.return_value = {"key": "value"}  # Return a serializable dictionary
    mock_db.collection.return_value.document.return_value = mock_document

    response = client.post("/swan", headers=headers, json=payload)
    assert response.status_code == 200
    assert "cmd" in response.get_json()

@patch('app.views.main.db')
def test_post_swan_json_set_cfg_failure(mock_db, client):
    headers = {
        "Wep-Imei": "123111111113",
        "Content-Type": "application/json"
    }
    payload = {
        "cmd_res": {
            "type": "set_cfg",
            "id": "session_123111111113_1",
            "res_code": 1
        }
    }

    # Mock the Firestore document get and update methods
    mock_document = MagicMock()
    mock_document.get.return_value.exists = True
    mock_document.get.return_value.to_dict.return_value = {"key": "value"}  # Return a serializable dictionary
    mock_db.collection.return_value.document.return_value = mock_document

    response = client.post("/swan", headers=headers, json=payload)
    assert response.status_code == 400