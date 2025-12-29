from scripts.fetch_data import fetch_user_events
import pandas as pd
import pickle
import os
from datetime import datetime

MODEL_DIR = "../models"

def train_model():
    # Fetch data
    df = fetch_user_events()
    if df.empty:
        print("No new data to train on. Skipping training.")
        return None

    # Example: simple product event count model
    product_features = df.groupby('product_id')['event_type'].count().to_frame()
    product_features = product_features / product_features.max()  # normalize

    # Save model with timestamp versioning
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_version_dir = os.path.join(MODEL_DIR, f"v{timestamp}")
    os.makedirs(model_version_dir, exist_ok=True)
    model_path = os.path.join(model_version_dir, "model.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(product_features, f)

    print(f"Model trained and saved to {model_path}")
    return model_path

def retrain_if_new_data():
    """
    Checks for new data (or simply retrains every run for demo purposes).
    Could be extended to check last training timestamp vs new data.
    """
    model_path = train_model()
    if model_path:
        print("Retraining complete.")
    else:
        print("No retraining needed.")

if __name__ == "__main__":
    retrain_if_new_data()
