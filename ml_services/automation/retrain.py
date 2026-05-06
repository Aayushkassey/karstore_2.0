import os
import sys
import ast
import json
import joblib
import traceback
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lightfm import LightFM
from lightfm.data import Dataset
from lightfm.evaluation import auc_score, precision_at_k, recall_at_k

DATA_DIR   = "ml_services/automation/data"
MODELS_DIR = "ml_services/automation/models"

def parse_interests(val):
    if pd.isna(val) or str(val).strip() in ["[]", ""]:
        return []
    try:
        parsed = ast.literal_eval(str(val))
        return [i.strip().lower().replace("-", " ") for i in parsed]
    except Exception:
        return []

def retrain():
    os.makedirs(MODELS_DIR, exist_ok=True)

    #1. LOAD --------------------------------------------------------------------------------
    print("Loading CSVs...")
    interactions = pd.read_csv(os.path.join(DATA_DIR, "interactions_export.csv"))
    users        = pd.read_csv(os.path.join(DATA_DIR, "users_export.csv"))
    products     = pd.read_csv(os.path.join(DATA_DIR, "products_export.csv"))

    print(f"  Interactions: {len(interactions)}")
    print(f"  Users:        {len(users)}")
    print(f"  Products:     {len(products)}")

    #2. CLEAN AND PREPARE -------------------------------------------------------------------------- 
    print("\nCleaning data...")
    products.columns     = products.columns.str.lower().str.strip()
    interactions.columns = interactions.columns.str.lower().str.strip()
    users.columns        = users.columns.str.lower().str.strip()

    products["product_id"] = products["id"].astype(int)
    
    interactions["product_id"] = interactions["product_id"].astype(int)
    interactions["interaction_timestamp"] = pd.to_datetime(
        interactions["interaction_timestamp"]
    )

    products['brand']    = products['brand'].fillna('unknown')
    products['category'] = products['category'].fillna('other')

    # ── 3. PRODUCT FEATURES ───────────────────────────────────────────────────
    print("\nProduct feature engineering...")
    products["category"] = products["category"].str.strip().str.lower()
    products["brand"]    = products["brand"].str.strip().str.lower()

    products["price_range"] = pd.cut(
        products["price"],
        bins=[0, 2500, 5000, 10000, 30000, float("inf")],
        labels=["budget", "low_mid", "mid", "high_mid", "premium"]
    ).astype(str)

    products["rating_band"] = pd.cut(
        products["rating"],
        bins=[0, 2.9, 3.3, 4.0, 4.5, 5.0],
        labels=["poor", "average", "good", "great", "excellent"]
    ).astype(str)

    # ── 4. USER FEATURES ──────────────────────────────────────────────────────
    print("\nUser feature engineering...")
    users["registration_date"] = pd.to_datetime(
        users["registration_date"], format='ISO8601'
    )
    today = interactions["interaction_timestamp"].max()
    users["tenure_days"] = (today - users["registration_date"]).dt.days

    users["tenure_band"] = pd.cut(
        users["tenure_days"],
        bins=[0, 15, 30, 90, 270, float("inf")],
        labels=["new", "early", "growing", "established", "loyal"]
    ).astype(str)

    users["age_group"] = pd.cut(
        users["age"],
        bins=[0, 25, 35, 45, 60, float("inf")],
        labels=["18_25", "26_35", "36_45", "46_60", "60+"]
    ).astype(str)

    users["interests_parsed"] = users["interests"].apply(parse_interests)

    # ── 5. INTERACTION WEIGHTS ────────────────────────────────────────────────
    weight_map = {"view": 1, "wishlist": 2, "cart": 3, "purchase": 5}
    interactions["weight"] = interactions["event_type"].map(weight_map).fillna(1)

    # ── 6. TRAIN TEST SPLIT ───────────────────────────────────────────────────
    print("\nTrain/test split...")
    # interactions = interactions.sort_values("interaction_timestamp").reset_index(drop=True)

    # split = int(len(interactions) * 0.8)
    # train_events = interactions.iloc[:split]
    # test_events  = interactions.iloc[split:]
    interactions = interactions.sort_values("interaction_timestamp").reset_index(drop=True)

    interactions = interactions.drop_duplicates(
        subset = ["user_id", "product_id"],
        keep = "last"
    ).sort_values("interaction_timestamp").reset_index(drop=True)

    split = int(len(interactions)*0.8)
    train_events = interactions.iloc[:split]
    test_events = interactions.iloc[split:]

    train_pairs = set(zip(train_events["user_id"], train_events["product_id"]))
    test_pairs = set(zip(test_events["user_id"], test_events["product_id"]))
    overlap = train_pairs & test_pairs

    print(f"overlap: {len(overlap)}")
    print(f"Train events: {len(train_events)}")
    print(f"Test events: {len(test_events)}")   

    print(f"  Train: {len(train_events)}, Test: {len(test_events)}")

    # ── 7. BUILD LIGHTFM DATASET ──────────────────────────────────────────────
    print("\nBuilding LightFM dataset...")
    event_users = interactions["user_id"].unique()
    event_items = interactions["product_id"].unique()

    all_user_interests = set()
    for interests_list in users["interests_parsed"]:
        for interest in interests_list:
            all_user_interests.add(interest.strip().lower())

    dataset = Dataset()
    dataset.fit(
        users=event_users,
        items=event_items,
        item_features=[
            *[f"category:{c}" for c in products["category"].unique()],
            *[f"brand:{b}"    for b in products["brand"].unique()],
            *[f"price:{p}"    for p in products["price_range"].unique()],
            *[f"rating:{r}"   for r in products["rating_band"].unique()],
        ],
        user_features=[
            *[f"gender:{g}"   for g in users["gender"].unique()],
            *[f"tenure:{t}"   for t in users["tenure_band"].unique()],
            *[f"age:{a}"      for a in users["age_group"].unique()],
            *[f"interest:{i}" for i in all_user_interests],
        ],
    )

    n_users, n_items = dataset.interactions_shape()
    print(f"  Registered users: {n_users}, items: {n_items}")

    # ── 8. INTERACTION MATRICES ───────────────────────────────────────────────
    print("\nBuilding interaction matrices...")

    def build_interactions(df, dataset):
        return dataset.build_interactions(
            (row["user_id"], row["product_id"], row["weight"])
            for _, row in df.iterrows()
        )

    train_interactions, _ = build_interactions(train_events, dataset)
    test_interactions,  _ = build_interactions(test_events,  dataset)

    train_interactions = train_interactions.tocsr()
    test_interactions  = test_interactions.tocsr()

    # ── 9. ITEM FEATURES ──────────────────────────────────────────────────────
    print("\nBuilding item feature matrix...")
    item_features = dataset.build_item_features(
        (
            row["product_id"],
            [
                f"category:{row['category']}",
                f"brand:{row['brand']}",
                f"price:{row['price_range']}",
                f"rating:{row['rating_band']}",
            ]
        )
        for _, row in products.iterrows()
        if row["product_id"] in set(event_items)
    )

    # ── 10. USER FEATURES ─────────────────────────────────────────────────────
    print("\nBuilding user feature matrix...")
    users_filtered = users[users["user_id"].isin(event_users)].copy()

    _, user_feature_map, _, _ = dataset.mapping()
    registered_interests = {
        feat for feat in user_feature_map.keys()
        if feat.startswith("interest:")
    }

    def get_user_features(row):
        feats = [
            f"gender:{row['gender']}",
            f"tenure:{row['tenure_band']}",
            f"age:{row['age_group']}",
        ]
        for interest in row["interests_parsed"]:
            feat = f"interest:{interest.strip().lower()}"
            if feat in registered_interests:
                feats.append(feat)
        return feats

    user_features = dataset.build_user_features(
        (row["user_id"], get_user_features(row))
        for _, row in users_filtered.iterrows()
    )

    # ── 11. TRAIN ─────────────────────────────────────────────────────────────
    print("\nTraining LightFM...")
    model = LightFM(
        no_components=32,
        loss="warp",
        learning_rate=0.05,
        item_alpha=1e-3,
        user_alpha=1e-3,
        random_state=42,
    )

    EPOCHS  = 40
    PATIENCE = 10
    train_aucs = []
    test_aucs  = []
    best_test_auc = 0
    best_epoch    = 0
    no_improve    = 0
    best_model_path = os.path.join(MODELS_DIR, "lightfm_best.pkl")

    for epoch in range(1, EPOCHS + 1):
        try:
            model.fit_partial(
                interactions  = train_interactions,
                user_features = user_features,
                item_features = item_features,
                epochs = 1,
            )
        except Exception as e:
            print(f"Crash at epoch {epoch}: {e}")
            traceback.print_exc()
            sys.exit(1)

        train_auc = auc_score(
            model, train_interactions,
            user_features=user_features,
            item_features=item_features,
            num_threads=1,
        ).mean()

        test_auc = auc_score(
            model, test_interactions,
            train_interactions=train_interactions,
            user_features=user_features,
            item_features=item_features,
            num_threads=1,
        ).mean()

        train_aucs.append(train_auc)
        test_aucs.append(test_auc)
        print(f"  Epoch {epoch:>2} train={train_auc:.4f} test={test_auc:.4f}")

        if test_auc > best_test_auc:
            best_test_auc = test_auc
            best_epoch    = epoch
            no_improve    = 0
            joblib.dump(model, best_model_path)
            print(f"Best model saved at epoch {epoch}")
        else:
            no_improve += 1
            if no_improve >= PATIENCE:
                print(f"\nEarly stopping at epoch {epoch}")
                print(f"Best epoch: {best_epoch}, test AUC: {best_test_auc:.4f}")
                break

    # ── 12. EVALUATE ──────────────────────────────────────────────────────────
    print("\nEvaluating...")
    model = joblib.load(best_model_path)

    p_at_k = precision_at_k(
        model, test_interactions,
        train_interactions=train_interactions,
        user_features=user_features,
        item_features=item_features,
        k=10, num_threads=1,
    ).mean()

    r_at_k = recall_at_k(
        model, test_interactions,
        train_interactions=train_interactions,
        user_features=user_features,
        item_features=item_features,
        k=10, num_threads=1,
    ).mean()

    print(f"  Best epoch:    {best_epoch}")
    print(f"  Train AUC:     {train_aucs[best_epoch-1]:.4f}")
    print(f"  Test AUC:      {best_test_auc:.4f}")
    print(f"  Precision@10:  {p_at_k:.4f}")
    print(f"  Recall@10:     {r_at_k:.4f}")

    # ── 13. SAVE DATASET + META ───────────────────────────────────────────────
    dataset_path = os.path.join(MODELS_DIR, "lightfm_dataset.pkl")
    joblib.dump(dataset, dataset_path)

    meta = {
        "best_epoch":      int(best_epoch),
        "no_components":   32,
        "loss":            "warp",
        "learning_rate":   0.05,
        "item_alpha":      1e-3,
        "user_alpha":      1e-3,
        "best_test_auc":   round(float(best_test_auc), 4),
        "train_auc":       round(float(train_aucs[best_epoch-1]), 4),
        "precision_at_10": float(p_at_k),
        "recall_at_10":    float(r_at_k),
        "item_features":   ["category", "brand", "price_range", "rating_band"],
        "user_features":   ["gender", "tenure_band", "age_group", "interests"],
        "weight_map":      {"view": 1, "wishlist": 2, "cart": 3, "purchase": 5},
    }
    meta_path = os.path.join(MODELS_DIR, "lightfm_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    # ── 14. LEARNING CURVE ────────────────────────────────────────────────────
    actual_epochs = len(train_aucs)
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, actual_epochs+1), train_aucs, label="Train AUC", marker="o")
    plt.plot(range(1, actual_epochs+1), test_aucs,  label="Test AUC",  marker="o")
    plt.axvline(x=best_epoch, color="red", linestyle="--",
                label=f"Best epoch {best_epoch}")
    plt.xlabel("Epoch")
    plt.ylabel("AUC")
    plt.title("LightFM Learning Curve")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    curve_path = os.path.join(MODELS_DIR, "learning_curve.png")
    plt.savefig(curve_path, dpi=150)
    print(f"\nLearning curve saved: {curve_path}")

    print("\nSaved:")
    print(f"  {best_model_path}")
    print(f"  {dataset_path}")
    print(f"  {meta_path}")

    return {
        "best_epoch":    best_epoch,
        "best_test_auc": best_test_auc,
        "model_path":    best_model_path,
        "dataset_path":  dataset_path,
        "meta_path":     meta_path,
    }

if __name__ == "__main__":
    retrain()