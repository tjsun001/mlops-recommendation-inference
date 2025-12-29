import pickle
import os

MODEL_DIR = "../models"

def load_latest_model():
    versions = sorted(os.listdir(MODEL_DIR))
    latest = versions[-1]
    model_path = os.path.join(MODEL_DIR, latest, "model.pkl")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model

def recommend(product_id, top_n=5):
    model = load_latest_model()
    if product_id not in model.index:
        return []
    # simple example: return top_n products with highest counts
    similar = model.sort_values(by='event_type', ascending=False)
    return similar.index.tolist()[:top_n]

if __name__ == "__main__":
    recommendations = recommend(product_id=1)
    print(f"Recommended: {recommendations}")
