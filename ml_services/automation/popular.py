import os
import pandas as pd

OUTPUT_DIR = "ml_services/automation/data"

WEIGHT_MAP = {
    "view":     1,
    "wishlist": 2,
    "cart":     3,
    "purchase": 5,
}

def compute_popular(top_n: int = 20) -> str:
    """
    Compute popular products from interactions CSV.
    Returns path to saved popular_products.csv.
    """
    print("Computing popular products...")

    interactions_path = os.path.join(OUTPUT_DIR, "interactions_export.csv")
    df = pd.read_csv(interactions_path)

    # Apply weights
    df["weight"] = df["event_type"].map(WEIGHT_MAP).fillna(1)

    # Sum weights per product
    popular = (
        df.groupby("product_id")["weight"]
        .sum()
        .reset_index()
        .rename(columns={"weight": "total_score"})
        .sort_values("total_score", ascending=False)
        .head(top_n)
    )

    popular["product_id"] = popular["product_id"].astype(int)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "popular_products.csv")
    popular[["product_id", "total_score"]].to_csv(output_path, index=False)

    print(f"  Top {top_n} popular products computed.")
    print(f"  Top 5: {popular['product_id'].head(5).tolist()}")

    return output_path

if __name__ == "__main__":
    compute_popular()