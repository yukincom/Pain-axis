#!/usr/bin/env python3
"""Recompute descriptive statistics from the published numeric-only 420-row CSV."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

COLUMNS = ["id", "category", "stratum", "perspective", "intensity", "projection", "z"]

def summarize(csv_bytes):
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    if reader.fieldnames != COLUMNS:
        raise ValueError("Unexpected columns")
    rows = list(reader)
    if len(rows) != 420 or len({r["id"] for r in rows}) != 420:
        raise ValueError("Expected 420 unique scenario IDs")
    groups = {}
    for row in rows:
        row["projection"] = float(row["projection"])
        row["z"] = float(row["z"])
        if not all(math.isfinite(row[k]) for k in ("projection", "z")):
            raise ValueError("Non-finite score")
        groups.setdefault(row["stratum"], []).append(row)
    expected = {"self_directed": 220, "neutral_filler": 100, "vicarious_empathic": 100}
    if {k: len(v) for k, v in groups.items()} != expected:
        raise ValueError("Unexpected strata or counts")
    mean = math.fsum(r["projection"] for r in rows) / len(rows)
    denominator = math.sqrt(math.fsum((r["projection"] - mean) ** 2 for r in rows) / len(rows)) + 1e-8
    max_error = max(abs(r["z"] - (r["projection"] - mean) / denominator) for r in rows)
    if max_error > 1e-10:
        raise ValueError("Published z scores do not match whole-set normalization")
    positives = groups["self_directed"]
    def auc(negatives):
        wins = sum((p["z"] > n["z"]) + 0.5 * (p["z"] == n["z"]) for p in positives for n in negatives)
        return wins / (len(positives) * len(negatives))
    return {
        "study_date": "2026-09-21",
        "scope": "Descriptive screening of all 420 public scenarios; not a train/test split or cross-validated AUC",
        "model": "mlx-community/Josiefied-Qwen3-14B-abliterated-v3-4bit",
        "layer_zero_based": 21,
        "direction": "Unit-normalized S2 final_token direction",
        "activation_readout": "Final token",
        "outputs_generated": False,
        "row_count": len(rows),
        "groups": {k: {"n": len(groups[k]), "mean_z": math.fsum(r["z"] for r in groups[k]) / len(groups[k])} for k in expected},
        "auc": {
            "self_vs_neutral": auc(groups["neutral_filler"]),
            "self_vs_vicarious": auc(groups["vicarious_empathic"]),
            "self_vs_all_nonself": auc(groups["neutral_filler"] + groups["vicarious_empathic"])
        },
        "normalization": {
            "formula": "(projection - mean_420) / (population_std_420 + 1e-8)",
            "projection_mean": mean,
            "denominator": denominator,
            "max_recomputed_z_error": max_error
        },
        "numeric_csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "source_data": {
            "repository": "https://github.com/valen-research/Pain-axis",
            "commit": "8d1649c03a63a39c9aa092532c376800cc4a3863",
            "path": "datasets/4.1_self_other_420_scenarios.json",
            "sha256": "901ea558faf34c69caff59321775723e20bebf49a77d20070f6b85a0368a3291"
        }
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path, default=Path(__file__).resolve().parents[1] / "results" / "self-other-420-scores.csv")
    args = parser.parse_args()
    print(json.dumps(summarize(args.csv.read_bytes()), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
