from . import test
from flask import jsonify, render_template, current_app, request
import pandas as pd
from tests import tester
from models import Stock
from datetime import datetime

@test.route('/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello from testing"})

@test.route("/run_all_tests", methods=["GET"])
def run_tests():
    success, output, results = tester.run_all_tests()
    return render_template(
        'pages/tests/run_all_tests.html',
        success=success,
        output = output,
        results = results
    )

@test.route('/post_to_db', methods=['GET', 'POST'])
def post_to_db():
    if request.method == 'GET':
        data = pd.DataFrame({
            "date": [datetime.today().date()],
            "open": [1],
            "high": [2],
            "low": [1],
            "close": [2],
            "volume": [3],
            "dividends": [0],
            "stock_splits": [0],
            "ticker": ["TEST"]
        })
    else:
        data = request.get_json()
        data = pd.DataFrame(data)

    engine = current_app.engine # type: ignore[attr-defined]
    with engine.begin() as connection:
        data.to_sql('stock', connection, if_exists='append', index=False)

    return jsonify({"result": "success"})


@test.route('/get_stock_data')
def get_stock_data():
    session_factory = current_app.db_session  # type: ignore[attr-defined]
    session = session_factory()
    latest = session.query(Stock).filter_by(ticker=str("TEST")).order_by(Stock.date.desc()).first()
    return jsonify({"ticker": latest.ticker,"date": latest.date, "id": latest.id})