"""
Tests for generate_tsv_file in app/helper/file_helper.py

These tests target three specific failure modes that can cause rows to be
silently dropped or the file to be left in a corrupt/partial state:

  1. Inconsistent row keys  - columns come from defaults_keys (a fixed schema),
     so any key not in that schema is silently ignored regardless of row order.

  2. Unhandled exception mid-loop - if writerow() raises, the exception is
     caught and logged, and all remaining rows after the failing one are never
     written.

  3. Concurrent writes - when each caller supplies its own output_dir the two
     requests write to completely separate directories and can never mix data.
"""

import csv
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_COLUMNS = ["id", "name"]


def _read_tsv(file_path: Path) -> list[list[str]]:
    """Read every row from a TSV file and return as a list of lists."""
    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        return list(reader)


# ---------------------------------------------------------------------------
# Fixture: patch defaults_keys so "TESTFILE" has a known schema.
# All tests pass output_dir=tmp_path so no real project paths are touched.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_defaults_keys():
    """Inject a minimal schema for the TESTFILE prefix used in all tests."""
    with patch("app.helper.file_helper.defaults_keys", {"TESTFILE": FAKE_COLUMNS}):
        yield


# ---------------------------------------------------------------------------
# Test 1: Inconsistent row keys -> silent column omission
# ---------------------------------------------------------------------------

class TestInconsistentRowKeys:
    """
    Columns are derived from defaults_keys, not from data[0].keys().
    Any key in a data row that is not in the schema is silently ignored.
    Any key in the schema that is missing from a data row produces "".
    """

    def test_extra_key_in_data_row_is_silently_dropped(self, tmp_path):
        from app.helper.file_helper import generate_tsv_file

        data = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob", "extra": "X"},  # "extra" not in schema
        ]
        generate_tsv_file(data, "TESTFILE", output_dir=tmp_path)

        written = _read_tsv(tmp_path / "TESTFILE_0.txt")
        assert len(written) == 2
        assert all(len(row) == 2 for row in written), (
            f"Expected 2 columns per row (matching schema), got: {written}"
        )
        assert "X" not in [cell for row in written for cell in row], (
            "The extra value should have been silently dropped but was found in output"
        )

    def test_missing_key_in_data_row_writes_empty_string(self, tmp_path):
        from app.helper.file_helper import generate_tsv_file

        data = [
            {"id": "1", "name": "Alice"},
            {"id": "2"},  # "name" missing -> should produce ""
        ]
        generate_tsv_file(data, "TESTFILE", output_dir=tmp_path)

        written = _read_tsv(tmp_path / "TESTFILE_0.txt")
        assert written[1] == ["2", ""], (
            f"Expected ['2', ''] for row with missing key, got: {written[1]}"
        )


# ---------------------------------------------------------------------------
# Test 2: Exception mid-loop -> remaining rows are lost
# ---------------------------------------------------------------------------

class TestExceptionMidLoop:
    """
    The writerow() loop is wrapped in a try/except that logs the error and
    stops. If an exception is raised while writing row N, rows N+1 ... end are
    never written.
    """

    def test_exception_on_row_stops_all_subsequent_rows(self, tmp_path):
        from app.helper.file_helper import generate_tsv_file

        call_count = 0

        class Explodes:
            """A value whose __str__ raises after the first two successful calls."""
            def __str__(self):
                nonlocal call_count
                call_count += 1
                if call_count >= 3:  # row 0 ok, row 1 ok, row 2 blows up
                    raise ValueError("Simulated serialisation failure")
                return "safe_value"

        data = [
            {"id": "1", "name": Explodes()},  # row 0 - writes OK
            {"id": "2", "name": Explodes()},  # row 1 - writes OK
            {"id": "3", "name": Explodes()},  # row 2 - Explodes.__str__ raises
            {"id": "4", "name": "never"},     # row 3 - never reached
        ]

        # The exception is caught internally; no exception should propagate.
        generate_tsv_file(data, "TESTFILE", output_dir=tmp_path)

        file_path = tmp_path / "TESTFILE_0.txt"
        written = _read_tsv(file_path)
        ids_written = [row[0] for row in written if row]
        assert "4" not in ids_written, (
            "Row with id=4 should never have been written because the "
            "exception on row 3 should have aborted the loop"
        )


# ---------------------------------------------------------------------------
# Test 3: Per-request output_dir isolates concurrent writes
# ---------------------------------------------------------------------------

class TestConcurrentAppends:
    """
    When each caller passes its own output_dir, two concurrent requests write
    to completely separate directories and can never interleave or mix data.
    """

    def test_concurrent_writes_to_separate_dirs_are_fully_isolated(self, tmp_path):
        from app.helper.file_helper import generate_tsv_file

        dir_a = tmp_path / "session_a"
        dir_b = tmp_path / "session_b"

        batch_a = [{"id": str(i), "name": "A"} for i in range(50)]
        batch_b = [{"id": str(i), "name": "B"} for i in range(50)]

        errors: list[Exception] = []

        def write(data, out_dir):
            try:
                generate_tsv_file(data, "TESTFILE", output_dir=out_dir)
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=write, args=(batch_a, dir_a))
        t2 = threading.Thread(target=write, args=(batch_b, dir_b))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors, f"Threads raised exceptions: {errors}"

        rows_a = _read_tsv(dir_a / "TESTFILE_0.txt")
        rows_b = _read_tsv(dir_b / "TESTFILE_0.txt")

        assert len(rows_a) == 50, f"Session A: expected 50 rows, got {len(rows_a)}"
        assert len(rows_b) == 50, f"Session B: expected 50 rows, got {len(rows_b)}"

        names_in_a = {row[1] for row in rows_a if len(row) > 1}
        names_in_b = {row[1] for row in rows_b if len(row) > 1}
        assert names_in_a == {"A"}, f"Session A contains rows from unexpected sources: {names_in_a}"
        assert names_in_b == {"B"}, f"Session B contains rows from unexpected sources: {names_in_b}"
