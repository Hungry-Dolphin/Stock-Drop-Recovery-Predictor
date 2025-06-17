import pytest
from DropRecoveryPredictor.app import app

@pytest.fixture()
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture()
def runner():
    return app.test_cli_runner()

def test_404_response(client):
    response = client.get("/this_page_does_not_exist")
    assert b"404" in response.data