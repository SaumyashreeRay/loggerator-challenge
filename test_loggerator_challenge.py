import pytest
import re

from loggerator_challenge import app, get_loggerator_logs

@pytest.fixture
def client():
    app.config["TESTING"] = True
    client = app.test_client()
    yield client


def test_get_loggerator_logs_returns_list():
    logs = get_loggerator_logs()
    assert isinstance(logs, list)
    assert len(logs) > 0
    
def test_get_loggerator_logs_returns_expected_format():
    logs = get_loggerator_logs()
    assert all(isinstance(log, str) for log in logs)

def test_get_loggerator_logs_raises_exception_on_error():
    with pytest.raises(Exception):
        get_loggerator_logs("invalid_container_name")

def test_logs_endpoint_with_valid_params(client):
    response = client.get("/logs?code=200&method=POST&user=abc")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)

def test_logs_endpoint_with_valid_and_invalid_params(client):
    response = client.get("/logs?code=abc&method=POST&user=def")
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data

def test_logs_endpoint_has_descending_order(client):
    response = client.get("/logs?code=200&method=POST&user=abc")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)

    # Check if data is in descending time order
    timestamps = [entry['timestamp'] for entry in data]
    assert all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))

def test_logs_endpoint_response_status_code_filter(client):
    response = client.get("/logs?code=268&method=POST&user=abc")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)

    # Verify that all logs have status code 268
    status_codes = [re.search(r'\s(\d+)$', entry).group(1) for entry in data]
    assert all(code == '268' for code in status_codes)

def test_logs_endpoint_response_method_filter(client):
    response = client.get("/logs?code=200&method=POST&user=abc")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)

    # Verify that all logs have the method "POST"
    methods = [re.search(r'^\D+$', entry).group(1) for entry in data]
    assert all(method == 'POST' for method in methods)

def test_logs_endpoint_response_user_filter(client):
    response = client.get("/logs?code=200&method=POST&user=abcdef")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)

    # Verify that all logs have the user "abcdef"
    users = [re.search(r'^\D+$', entry).group(1) for entry in data]
    assert all(user == 'abcdef' for user in users)

def test_logs_endpoint_with_invalid_code_param(client):
    response = client.get("/logs?code=invalid")
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data

def test_logs_endpoint_with_invalid_method_param(client):
    response = client.get("/logs?method=123!")
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data

def test_logs_endpoint_with_invalid_user_param(client):
    response = client.get("/logs?user=admin!123")
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data