from utils.db import get_conn
import pandas as pd

def fetch_user_events():
    """
    Fetch user_events table from Postgres.
    """
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM user_events ORDER BY created_at", conn)
    conn.close()
    return df

if __name__ == "__main__":
    df = fetch_user_events()
    print(f"Fetched {len(df)} rows")
