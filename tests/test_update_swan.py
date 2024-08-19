import pytest
from flask import Flask
from dotenv import load_dotenv
import os
load_dotenv()

from app import create_app  # Adjust the import based on your app structure

@pytest.fixture
def client():
    app = create_app()  # Adjust this based on how you create your Flask app
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            # Initialize your database or other setup here if needed
            yield client

def test_update_swan(client):
    imei = "123111111113"
    url = f"/update/swan/{imei}"
    payload = {
        "autostart": 0,
        "ci_field_blacklist": 0,
        "clear_status_after_ul": 1,
        "collect_datalog_flags": 3,
        "collect_datalog_flags_2": 3,
        "collect_days": 16385,
        "collect_days_2": 0,
        "collect_duration": 300,
        "collect_duration_2": 300,
        "collect_flags": 0,
        "collect_flags_2": 0,
        "collect_hours": 0,
        "collect_hours_2": 0,
        "collect_jitter": 0,
        "collect_jitter_2": 0,
        "collect_max_num_meters": 5,
        "collect_max_num_meters_2": 5,
        "collect_mode": 8,
        "collect_mode_2": 0,
        "collect_months": 4095,
        "collect_months_2": 0,
        "collect_per_hour": 1,
        "collect_per_hour_2": 1,
        "collect_rssi_max": 127,
        "collect_rssi_max_2": 127,
        "collect_rssi_min": -108,
        "collect_rssi_min_2": -108,
        "collect_start_hour": 0,
        "collect_start_hour_2": 0,
        "collect_start_minute": 0,
        "collect_start_minute_2": 0,
        "collect_use_dll": 0,
        "collect_use_dll_2": 0,
        "collect_week_days": 0,
        "collect_week_days_2": 0,
        "collect_weeks": 0,
        "collect_weeks_2": 0,
        "daylightsaving_enable": 1,
        "device_tag": "",
        "imei": "123111111111113",
        "lwm2m_idle_time": 120,
        "lwm2m_lifetime": 150,
        "lwm2m_notify_retry_cnt": 2,
        "lwm2m_notify_timeout": 7,
        "lwm2m_notify_with_ack": 1,
        "nb1_apn": "",
        "nb1_apn_account_index": 0,
        "nb1_bands": "3,8,20",
        "nb1_plmn": "",
        "nb1_psm": 0,
        "nb1_psm_activetime": 0,
        "nb1_psm_tau": 0,
        "nb1_rai": 3,
        "nfc_fast_install": 1,
        "ntp_auto_sync": 0,
        "ntp_port": 123,
        "ntp_server": "0.europe.pool.ntp.org",
        "prefilter_devicetype": "",
        "prefilter_manufacturer": "",
        "quietmode": 0,
        "sync_rx": 1,
        "sync_rx_duration": 2000,
        "sync_rx_interval": 300,
        "sync_rx_max_time_gap": 3600,
        "sync_rx_meter": "12345678-WEP-02-02",
        "sync_rx_storage": 3600,
        "timezone": 4,
        "uart_sci": 0,
        "upload_account_index": 0,
        "upload_after_collect": 0,
        "upload_after_collect_2": 0,
        "upload_alarm_interval": 80,
        "upload_alarm_mask": 0,
        "upload_days": 16385,
        "upload_format": 2,
        "upload_format_spec_1": 4294967295,
        "upload_format_spec_2": 4294967295,
        "upload_format_spec_3": 4294967295,
        "upload_hours": 0,
        "upload_jitter": 0,
        "upload_local_port": 28028,
        "upload_method": 1,
        "upload_months": 4095,
        "upload_per_hour": 1,
        "upload_proto": 3,
        "upload_remote_port": 31031,
        "upload_retries": 2,
        "upload_server": "weptech-iot.de/swan2",
        "upload_start_hour": 0,
        "upload_start_minute": 0,
        "upload_week_days": 0,
        "upload_weeks": 0
    }

    response = client.post(url, json=payload)
    assert response.status_code == 201
    assert response.get_json() == {'message': 'Swan device created successfully!'}
    
    