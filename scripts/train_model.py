"""Train the versioned prototype model from the project root."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.model.train import train_model


if __name__ == "__main__":
    try:
        metadata = train_model()
        print(f"Trained model {metadata['model_version']}.")
    except FileExistsError:
        print("Model v1 already exists and was preserved; no overwrite performed.")
