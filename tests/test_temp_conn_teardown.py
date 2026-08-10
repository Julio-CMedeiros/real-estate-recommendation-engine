"""Regression coverage for the temp_conn fixture teardown (tests/conftest.py).

Postgres puts a connection into an aborted-transaction state after any failed
statement; every subsequent statement on that connection then fails with
InFailedSqlTransaction until a rollback happens. Before the fix, temp_conn's
teardown ran its cleanup DELETEs directly against a connection that could be
in this state, so the DELETEs silently failed (leaking rows into the next
test) and - because there was no try/finally - conn.close() never ran
(leaking the connection from the pool).

These two tests exercise that exact sequence: the first deliberately breaks
its connection, the second (a fresh temp_conn against the same engine) proves
no rows or aborted state leaked forward.
"""

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError


def test_a_temp_conn_survives_a_failed_statement(temp_conn):
    # Leave some rows so the teardown DELETEs have something to clean up.
    temp_conn.execute(
        text(
            "INSERT INTO api_keys (consumer_name, hashed_key) "
            "VALUES ('teardown-regression', 'not-a-real-hash')"
        )
    )

    # Deliberately trigger a failed statement, putting the connection into
    # Postgres' aborted-transaction state. The fixture teardown must recover
    # from this (via rollback()) rather than let the cleanup DELETEs fail
    # silently or skip conn.close().
    try:
        temp_conn.execute(text("SELECT * FROM this_table_does_not_exist"))
    except ProgrammingError:
        pass
    else:
        raise AssertionError("expected the bogus query to fail")


def test_b_next_test_sees_clean_state(temp_conn):
    # If the previous test's teardown had silently failed (pre-fix bug), the
    # 'teardown-regression' row inserted above would still be present here.
    count = temp_conn.execute(
        text("SELECT COUNT(*) FROM api_keys WHERE consumer_name = 'teardown-regression'")
    ).scalar_one()
    assert count == 0

    # Sanity: the connection itself is healthy, not stuck in aborted state.
    assert temp_conn.execute(text("SELECT 1")).scalar_one() == 1
