import pytest
from DropRecoveryPredictor.app import app
import bs4

@pytest.fixture()
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture()
def runner():
    return app.test_cli_runner()

def test_layout_templates(client):
    response = client.get("/")
    assert response.status_code == 200

    html = bs4.BeautifulSoup(response.text)

    assert b"This page makes use of the main.html layout" in response.data

    assert html.title.text == "Drop Recovery Predictor Homepage"