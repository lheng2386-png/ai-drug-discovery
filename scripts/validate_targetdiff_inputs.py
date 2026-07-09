#!/usr/bin/env python3
"""Validate EGFR 10 Å pockets against TargetDiff's PDBProtein parser."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "pockets" / "egfr" / "egfr_pocket_manifest.csv"
BACKENDS = {
    "targetdiff": {
        "parser": ROOT / "external" / "targetdiff" / "utils" / "data.py",
        "commit": "142f1eb7178480d435fe0b8cb95a99beb48997c7",
    },
    "decompdiff": {
        "parser": ROOT / "external" / "decompdiff" / "utils" / "data.py",
        "commit": "ed4e7d8202c077cc4bd1b9ca626e173c24007f2a",
    },
}
STANDARD_RESIDUES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}


def load_parser(backend: str):
    source = BACKENDS[backend]
    parser_path = source["parser"]
    if not parser_path.exists():
        raise RuntimeError(
            f"{backend} source is missing. Restore it at commit {source['commit']}."
        )
    if "long" not in np.__dict__:
        np.long = np.int64
    if "bool" not in np.__dict__:
        np.bool = np.bool_
    spec = importlib.util.spec_from_file_location(f"{backend}_utils_data", parser_path)
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
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--backend", choices=sorted(BACKENDS), default="targetdiff"
    )
    args = argument_parser.parse_args()
    parser = None
    parser_error = None
    try:
        parser = load_parser(args.backend)
    except ModuleNotFoundError as error:
        if args.backend != "decompdiff":
            raise
        parser_error = f"{type(error).__name__}: {error}"
    with MANIFEST.open(encoding="utf-8") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if float(row["radius_angstrom"]) == 10.0
        ]
    results = []
    for row in rows:
        path = MANIFEST.parent / row["pocket_file"]
        static = static_validate(path)
        result = {
            "pdb_id": row["pdb_id"],
            "variant": row["variant"],
            "path": str(path.relative_to(ROOT)),
            **static,
        }
        if parser is not None:
            parsed = parser(str(path)).to_dict_atom()
            if parsed["pos"].shape != (static["atom_count"], 3):
                raise RuntimeError(f"{args.backend} parser shape mismatch for {path}")
            result.update(
                {
                    "backend_position_shape": list(parsed["pos"].shape),
                    "backend_feature_count": int(parsed["element"].shape[0]),
                }
            )
        results.append(result)

    audit = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if parser is not None else "static_only",
        "backend": args.backend,
        "source_commit": BACKENDS[args.backend]["commit"],
        "radius_angstrom": 10.0,
        "validated_pocket_count": len(results),
        "backend_parser_executed": parser is not None,
        "backend_parser_error": parser_error,
        "pockets": results,
        "scope": (
            "Protein-pocket format validation only; no decomposition metadata, "
            "checkpoint, or generation run."
        ),
    }
    audit_path = ROOT / "data" / f"{args.backend}-egfr-input-audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
