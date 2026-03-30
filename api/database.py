import psycopg2
from psycopg2 import pool
import os
import time

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://asterisk:asterisk@db/asterisk")

_connection_pool = None

def get_connection_pool():
    global _connection_pool
    if _connection_pool is None:
        # Retry logic for pool creation
        for i in range(10):
            try:
                _connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
                print("Connection pool created successfully")
                break
            except Exception as e:
                print(f"Attempt {i+1}: Error creating connection pool: {e}")
                time.sleep(2)
        if _connection_pool is None:
            raise Exception("Could not initialize database connection pool")
    return _connection_pool

def get_db_conn():
    pool = get_connection_pool()
    # Retry logic for getting a connection from the pool
    for _ in range(5):
        try:
            return pool.getconn()
        except Exception:
            time.sleep(2)
    raise Exception("Could not connect to database")

def release_db_conn(conn):
    pool = get_connection_pool()
    pool.putconn(conn)
