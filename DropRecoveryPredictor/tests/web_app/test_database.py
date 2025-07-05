import json

import pytest
from app import FlaskApp

@pytest.fixture()
def client():
    with FlaskApp().app.test_client() as client:
        yield client

@pytest.fixture()
def runner():
    return FlaskApp().app.test_cli_runner()

def test_connection(client):
    response = client.get("/test/first_stock")
    assert response.status_code == 200

    content = json.loads(response.get_data(as_text=True))

    assert content["id"] == 1