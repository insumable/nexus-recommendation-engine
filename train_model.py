import duckdb
import numpy as np
import scipy.sparse as sparse
from implicit.als import AlternatingLeastSquares

print("Connecting to DuckDB...")
con = duckdb.connect("nexus.duckdb", read_only=True)

print("Fetching and mapping user and item IDs to integers...")
# ALS requires continuous integer indices for rows (users) and columns (items)
query = """
    SELECT 
        user_id, 
        item_id, 
        rating 
    FROM fact_reviews 
    WHERE rating >= 4.0;
"""
df = con.execute(query.strip()).fetchdf()
con.close()

print(f"Loaded {len(df)} positive interactions (4+ stars) into memory.")

# Convert string IDs to categorical integer codes
user_codes = df['user_id'].astype('category').cat.codes
item_codes = df['item_id'].astype('category').cat.codes

# Store the mappings so we can translate back to real IDs later
users_cat = df['user_id'].astype('category')
items_cat = df['item_id'].astype('category')

# Build the Sparse CSR Matrix
print("Building sparse user-item interaction matrix...")
rows = user_codes.values
cols = item_codes.values
data = np.ones(len(df), dtype=np.float32) # Implicit confidence score

num_users = user_codes.max() + 1
num_items = item_codes.max() + 1

interaction_matrix = sparse.csr_matrix((data, (rows, cols)), shape=(num_users, num_items))

print(f"Matrix shape: {interaction_matrix.shape} (Users x Items)")

# Initialize and train the ALS model
print("Training Alternating Least Squares (ALS) model...")
model = AlternatingLeastSquares(
    factors=64,          # Latent dimensions
    regularization=0.05,
    iterations=15,
    calculate_training_loss=True
)

# Fit the model on the sparse matrix
model.fit(interaction_matrix)

print("Training complete! Model successfully generated latent factors.")