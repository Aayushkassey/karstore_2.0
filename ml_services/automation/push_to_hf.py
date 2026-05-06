import os
from huggingface_hub import HfApi

HF_REPO_ID = os.environ.get("HF_REPO_ID", "kamalpokhara/srs-models")
HF_TOKEN   = os.environ.get("HF_TOKEN")
MODELS_DIR = "ml_services/automation/models"
DATA_DIR   = "ml_services/automation/data"

def push_to_hf():
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN env var not set")

    api = HfApi()

    files = [
        (os.path.join(MODELS_DIR, "lightfm_best.pkl"),    "lightfm_best.pkl"),
        (os.path.join(MODELS_DIR, "lightfm_dataset.pkl"), "lightfm_dataset.pkl"),
        (os.path.join(MODELS_DIR, "lightfm_meta.json"),   "lightfm_meta.json"),
        (os.path.join(DATA_DIR,   "popular_products.csv"),"popular_products.csv"),
    ]

    print(f"Pushing models to HF Hub: {HF_REPO_ID}")

    for local_path, repo_path in files:
        if not os.path.exists(local_path):
            print(f"  SKIP {local_path} — file not found")
            continue

        print(f"  Uploading {repo_path}...")
        api.upload_file(
            path_or_fileobj = local_path,
            path_in_repo    = repo_path,
            repo_id         = HF_REPO_ID,
            token           = HF_TOKEN,
            repo_type       = "model"
        )
        print(f"\n{repo_path} pushed")

    print("\nAll models pushed to HF Hub successfully.")

if __name__ == "__main__":
    push_to_hf()