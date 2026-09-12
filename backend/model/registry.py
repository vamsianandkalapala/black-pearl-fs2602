"""Immutable manifest helpers for versioned model artifacts."""

import json
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_MANIFEST_PATH = PROJECT_ROOT / "models" / "manifest.json"


def register_model_version(
    metadata: Dict[str, Any],
    manifest_path: Path = MODEL_MANIFEST_PATH,
) -> Dict[str, Any]:
    """Add a model version to the manifest without allowing overwrites."""
    manifest_path = Path(manifest_path)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {"models": []}

    if any(item["model_version"] == metadata["model_version"] for item in manifest["models"]):
        raise FileExistsError(f"Model version already exists: {metadata['model_version']}")

    manifest["models"].append(metadata)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata
