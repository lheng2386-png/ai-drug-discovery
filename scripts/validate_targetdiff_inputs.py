#!/usr/bin/env python3
"""Validate EGFR 10 Å pockets against TargetDiff's PDBProtein parser."""

from __future__ import annotations

import csv
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "pockets" / "egfr" / "egfr_pocket_manifest.csv"
TARGETDIFF_DATA = ROOT / "external" / "targetdiff" / "utils" / "data.py"
AUDIT = ROOT / "data" / "targetdiff-egfr-input-audit.json"
EXPECTED_COMMIT = "142f1eb7178480d435fe0b8cb95a99beb48997c7"
STANDARD_RESIDUES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}


def load_targetdiff_parser():
    if not TARGETDIFF_DATA.exists():
        raise RuntimeError(
            "TargetDiff source is missing. Restore external/targetdiff at "
            f"commit {EXPECTED_COMMIT}."
        )
    if "long" not in np.__dict__:
        np.long = np.int64
    if "bool" not in np.__dict__:
        np.bool = np.bool_
    spec = importlib.util.spec_from_file_location("targetdiff_utils_data", TARGETDIFF_DATA)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.PDBProtein


def static_validate(path: Path) -> dict:
    atom_lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("ATOM  ")
    ]
    if not atom_lines:
        raise RuntimeError(f"No ATOM records in {path}")
    residues = {(line[21], int(line[22:26]), line[26], line[17:20]) for line in atom_lines}
    residue_names = {item[3] for item in residues}
    unsupported = sorted(residue_names - STANDARD_RESIDUES)
    coordinates = np.array(
        [[float(line[30:38]), float(line[38:46]), float(line[46:54])] for line in atom_lines]
    )
    if unsupported:
        raise RuntimeError(f"Unsupported residues in {path}: {unsupported}")
    if not np.isfinite(coordinates).all():
        raise RuntimeError(f"Non-finite coordinates in {path}")
    if any(line.startswith("HETATM") for line in path.read_text().splitlines()):
        raise RuntimeError(f"HETATM records found in protein pocket {path}")
    return {
        "atom_count": len(atom_lines),
        "residue_count": len(residues),
        "chains": sorted({line[21].strip() for line in atom_lines}),
        "coordinate_min": coordinates.min(axis=0).round(3).tolist(),
        "coordinate_max": coordinates.max(axis=0).round(3).tolist(),
    }


def main() -> None:
    parser = load_targetdiff_parser()
    with MANIFEST.open(encoding="utf-8") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if float(row["radius_angstrom"]) == 10.0
        ]
    results = []
    for row in rows:
        path = MANIFEST.parent / row["pocket_file"]
        static = static_validate(path)
        parsed = parser(str(path)).to_dict_atom()
        if parsed["pos"].shape != (static["atom_count"], 3):
            raise RuntimeError(f"TargetDiff parser shape mismatch for {path}")
        results.append(
            {
                "pdb_id": row["pdb_id"],
                "variant": row["variant"],
                "path": str(path.relative_to(ROOT)),
                **static,
                "targetdiff_position_shape": list(parsed["pos"].shape),
                "targetdiff_feature_count": int(parsed["element"].shape[0]),
            }
        )

    audit = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "targetdiff_commit": EXPECTED_COMMIT,
        "radius_angstrom": 10.0,
        "validated_pocket_count": len(results),
        "pockets": results,
        "scope": "Static input compatibility only; no checkpoint or generation run.",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
