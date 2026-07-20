from __future__ import annotations

import os
from typing import Any

import psycopg2
import psycopg2.extras


def get_connection() -> Any:
    dsn = os.environ.get(
        "SOLGREEN_DATABASE_URL",
        "postgresql://solgreen:solgreen@localhost:5432/solgreen",
    )
    return psycopg2.connect(dsn)


def execute_script(sql: str, conn: Any | None = None) -> None:
    close = False
    if conn is None:
        conn = get_connection()
        close = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        if close:
            conn.close()
