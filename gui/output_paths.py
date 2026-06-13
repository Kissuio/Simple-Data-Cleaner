"""Output folder naming helpers for generated chart pictures."""

from hashlib import md5
from pathlib import Path
import re
import unicodedata


OUTPUT_PICTURE_SUFFIX = "_output_picture"


def dataset_output_folder_name(file_path):
    """Return an English-safe output folder name for one dataset file."""
    stem = Path(file_path).stem if file_path else "dataset"
    normalized = unicodedata.normalize("NFKD", stem)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^A-Za-z0-9]+", "_", ascii_text).strip("_")
    if not safe:
        digest = md5(stem.encode("utf-8")).hexdigest()[:8]
        safe = f"dataset_{digest}"
    return f"{safe}{OUTPUT_PICTURE_SUFFIX}"


def dataset_output_picture_dir(file_path, base_dir="output"):
    """Return the per-dataset chart picture directory under the output root."""
    return Path(base_dir) / dataset_output_folder_name(file_path)
