import os
import pymysql
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Create a connection to the MyHotel database."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

_conn = None


def _connection():
    global _conn
    if _conn is None:
        _conn = get_connection()
        _conn.autocommit(True)
    _conn.ping(reconnect=True)
    return _conn


def query(sql, args=()):
    with _connection().cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def execute(sql, args=()):
    with _connection().cursor() as cur:
        cur.execute(sql, args)
        return cur.lastrowid


@contextmanager
def transaction():
    conn = _connection()
    conn.begin()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def close():
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
