import pytest
import os
import contextlib
import io
import sys

class APITestCollector:
    def __init__(self):
        self.results = []

    @pytest.hookimpl
    def pytest_runtest_logreport(self, report):
        # only care about the actual test call (ignore setup/teardown)
        if report.when == "call":
            self.results.append(
                {
                    "nodeid": report.nodeid,        # e.g. tests/test_api.py::test_login
                    "outcome": report.outcome,      # "passed", "failed", "skipped"
                    "duration": report.duration,    # seconds (float)
                    "longrepr": str(report.longrepr) if report.failed else None
                }
            )

def run_all_tests(pytest_args=None):
    b_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Add it to sys.path so imports work
    if b_dir not in sys.path:
        sys.path.insert(0, b_dir)


    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_dirs = [
        os.path.join(base_dir, "predictors"),
        os.path.join(base_dir, "web_app")
    ]

    test_paths = [os.path.abspath(d) for d in test_dirs]

    # Prepare pytest arguments:
    # - '-q' for quiet, '-s' to show print output immediately
    args = ["-q", "-s"] + test_paths
    if pytest_args:
        args.extend(pytest_args)

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        collector = APITestCollector()
        code = pytest.main(args, plugins=[collector])

    # Return (success bool, captured output, collected test results)
    return code == 0, buffer.getvalue(), collector.results