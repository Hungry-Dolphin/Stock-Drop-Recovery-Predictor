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
    response = client.get("/first_stock")
    assert response.status_code == 200