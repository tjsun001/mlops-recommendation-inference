import psycopg2
from psycopg2 import OperationalError

def get_conn():
    """
    Connect to local Postgres database. Replace values with your DB credentials.
    """
    try:
        conn = psycopg2.connect(
            host="localhost",           # or your EC2 host / Docker service
            port=5432,
            database="postgres",
            user="myuser02",
            password="password"
        )
        return conn
    except OperationalError as e:
        print("Error connecting to Postgres:", e)
        raise
