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

def test_post_stock(client):
    post = client.get("/test/post_to_db")
    assert post.status_code == 200

    content = json.loads(post.get_data(as_text=True))

    assert content["result"] == "success"

    get = client.get("/test/get_stock_data")
    assert get.status_code == 200

    content = json.loads(get.get_data(as_text=True))
    assert content["ticker"] == "TEST"