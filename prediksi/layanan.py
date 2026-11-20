"""Fungsi pembantu: memuat model dan ringkasan hasil pelatihan (dibaca sekali lalu disimpan di memori)."""
import json
from functools import lru_cache
from pathlib import Path

import joblib

FOLDER_ML = Path(__file__).resolve().parent / "ml"


@lru_cache(maxsize=1)
def muat_ringkasan():
    return json.loads((FOLDER_ML / "ringkasan.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def muat_model():
    return joblib.load(FOLDER_ML / "model_bbm.joblib")