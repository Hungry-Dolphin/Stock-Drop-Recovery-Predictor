from datetime import datetime, timedelta
import pandas as pd
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
    ticker = 'TEST'
    data = {
        "date": [datetime.today().date()- timedelta(days=1), datetime.today().date()- timedelta(days=2)], # Minus one day since we only calc previous days
        "open": [270, 250],
        "high": [280, 260],
        "low": [200, 200],
        "close": [250, 200],
        "volume": [3000, 40000],
        "dividends": [0, 0],
        "stock_splits": [0, 0],
        "ticker": ["TEST", "TEST"]
    }
    # Insert fake drop in database
    post = client.post("/test/post_to_db", json=data)
    assert post.status_code == 200

    # Calculate the results of this fake drop
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    prediction = FlaskApp().prediction_model.detect_and_predict_drop(df, ticker)
    print(prediction)