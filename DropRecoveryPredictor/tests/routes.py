from . import test
from flask import jsonify, render_template, current_app

from tests import tester
from models import Stock


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

@test.route('/first_stock')
def first_stock():
    session_factory = current_app.db_session # type: ignore[attr-defined]
    session = session_factory()
    first_hit = session.query(Stock).first()
    return jsonify({"ticker": first_hit.ticker, "id": first_hit.id})