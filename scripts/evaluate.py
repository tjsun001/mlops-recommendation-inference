from train import train_model
from inference import recommend

# Simple metric: check if some recommendations exist
train_model()
rec = recommend(product_id=1)
print("Sample recommendations:", rec)
