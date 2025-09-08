# -*- coding: utf-8 -*-
import yaml
from pathlib import Path

def load_scoring_profile(profile_name: str, base_path: Path = None) -> dict:
    base = base_path or Path(__file__).resolve().parents[1] / "configs" / "scoring.yaml"
    data = yaml.safe_load(base.read_text(encoding="utf-8"))
    prof = data.get("profiles", {}).get(profile_name)
    if not prof:
        raise ValueError(f"Scoring profile not found: {profile_name}")
    return {"global": data.get("global", {}), "profile": prof}
