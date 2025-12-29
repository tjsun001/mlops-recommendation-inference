from utils.db import get_conn
import random
from datetime import datetime, timedelta

NUM_USERS = 10
NUM_PRODUCTS = 10
NUM_EVENTS = 50  # total events to insert

EVENT_TYPES = ["view", "purchase", "add_to_cart"]

def generate_events():
    events = []
    for _ in range(NUM_EVENTS):
        user_id = random.randint(1, NUM_USERS)
        product_id = random.randint(1, NUM_PRODUCTS)
        event_type = random.choice(EVENT_TYPES)
        # random timestamp in the last 30 days
        created_at = datetime.now() - timedelta(days=random.randint(0, 30))
        events.append((user_id, product_id, event_type, created_at))
    return events

def seed_data():
    conn = get_conn()
    cur = conn.cursor()
    
    # Create table if it doesn't exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_events (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        product_id INT NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Insert synthetic events
    events = generate_events()
    for user_id, product_id, event_type, created_at in events:
        cur.execute("""
        INSERT INTO user_events (user_id, product_id, event_type, created_at)
        VALUES (%s, %s, %s, %s)
        """, (user_id, product_id, event_type, created_at))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {len(events)} synthetic events into user_events table.")

if __name__ == "__main__":
    seed_data()
