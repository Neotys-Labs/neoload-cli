import glob
import os

import pytest


@pytest.fixture(autouse=True)
def cleanup_actual_report_files():
    """Report tests write their generated output straight into
    tests/resources/report/ (actual_*, raw_actual_*) to compare it against the
    checked-in expected_*/raw_expected_* fixtures. Remove those generated
    files after each test, pass or fail, so they don't linger as untracked
    files on disk."""
    yield
    for pattern in ('tests/resources/report/actual_*', 'tests/resources/report/raw_actual_*'):
        for path in glob.glob(pattern):
            os.remove(path)
