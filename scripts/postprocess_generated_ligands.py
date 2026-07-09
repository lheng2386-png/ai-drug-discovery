#!/usr/bin/env python3
"""Normalize generated ligand outputs into SDF, SMILES/CSV, and properties CSV.

Inputs can be one or more directories containing SDF files, individual SDF
files, and optionally DecompDiff ``result.pt`` files. The script sanitizes
molecules with RDKit, removes invalid/disconnected/duplicate structures, and
writes the three first-batch deliverables:

- generated_egfr_candidates.sdf
- generated_egfr_candidates.csv
- basic_properties.csv
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, QED, rdMolDescriptors


@dataclass
class Candidate:
    mol: Chem.Mol
    source_model: str
    source_file: str
    source_record: str


def iter_sdf_files(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        for matched in glob.glob(raw):
            path = Path(matched)
            if path.is_dir():
                yield from sorted(path.rglob("*.sdf"))
            elif path.is_file() and path.suffix.lower() == ".sdf":
                yield path


def load_sdf_candidates(paths: Iterable[str], source_model: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    for sdf_path in iter_sdf_files(paths):
        supplier = Chem.SDMolSupplier(str(sdf_path), removeHs=False, sanitize=False)
        for idx, mol in enumerate(supplier):
            if mol is None:
                continue
            candidates.append(
                Candidate(
                    mol=mol,
                    source_model=source_model,
                    source_file=str(sdf_path),
                    source_record=str(idx),
                )
            )
    return candidates


def load_decompdiff_pt_candidates(paths: Iterable[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    matched_paths = [Path(p) for raw in paths for p in glob.glob(raw)]
    if not matched_paths:
        return candidates
    try:
        import torch
    except ImportError as exc:
        raise SystemExit(
            "Reading DecompDiff .pt outputs requires torch. "
            "Run inside the decompdiff/targetdiff environment or install torch."
        ) from exc

    for pt_path in matched_paths:
        try:
            obj = torch.load(str(pt_path), map_location="cpu", weights_only=False)
        except TypeError:
            obj = torch.load(str(pt_path), map_location="cpu")
        if not isinstance(obj, list):
            continue
        for idx, row in enumerate(obj):
            if isinstance(row, dict) and row.get("mol") is not None:
                candidates.append(
                    Candidate(
                        mol=row["mol"],
                        source_model="DecompDiff",
                        source_file=str(pt_path),
                        source_record=str(idx),
                    )
                )
    return candidates


def sanitize_and_canonicalize(mol: Chem.Mol) -> tuple[Chem.Mol | None, str, str]:
    try:
        work = Chem.Mol(mol)
        Chem.SanitizeMol(work)
        smiles = Chem.MolToSmiles(Chem.RemoveHs(work), canonical=True, isomericSmiles=True)
        if not smiles or "." in smiles:
            return None, "", "empty_or_disconnected"
        canonical = Chem.MolFromSmiles(smiles)
        if canonical is None:
            return None, "", "canonical_parse_failed"
        return canonical, smiles, ""
    except Exception as exc:  # RDKit raises several C++ exception wrappers.
        return None, "", f"sanitize_failed:{type(exc).__name__}"


def mol_props(mol: Chem.Mol) -> dict[str, str | float | int]:
    return {
        "num_heavy_atoms": mol.GetNumHeavyAtoms(),
        "num_atoms": mol.GetNumAtoms(),
        "molecular_weight": Descriptors.MolWt(mol),
        "exact_mol_wt": Descriptors.ExactMolWt(mol),
        "clogp": Crippen.MolLogP(mol),
        "tpsa": rdMolDescriptors.CalcTPSA(mol),
        "qed": QED.qed(mol),
        "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol),
        "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
        "ring_count": Lipinski.RingCount(mol),
        "aromatic_ring_count": Lipinski.NumAromaticRings(mol),
        "formal_charge": Chem.GetFormalCharge(mol),
        "fraction_csp3": rdMolDescriptors.CalcFractionCSP3(mol),
    }


def stable_candidate_id(source_model: str, smiles: str) -> str:
    digest = hashlib.sha1(f"{source_model}|{smiles}".encode("utf-8")).hexdigest()[:12]
    return f"EGFR-GEN-{digest}"


def write_outputs(
    candidates: list[Candidate],
    out_prefix: Path,
    target_id: str,
    target_variant: str,
    pocket_id: str,
) -> dict:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    sdf_path = out_prefix.with_suffix(".sdf")
    candidates_csv = out_prefix.with_suffix(".csv")
    props_csv = out_prefix.parent / "basic_properties.csv"
    audit_path = out_prefix.parent / "postprocess_audit.json"

    valid_rows: list[dict] = []
    invalid_rows: list[dict] = []
    seen: set[str] = set()

    for raw_idx, cand in enumerate(candidates):
        mol, smiles, reason = sanitize_and_canonicalize(cand.mol)
        if mol is None:
            invalid_rows.append(
                {
                    "raw_index": raw_idx,
                    "source_model": cand.source_model,
                    "source_file": cand.source_file,
                    "source_record": cand.source_record,
                    "invalid_reason": reason,
                }
            )
            continue
        if smiles in seen:
            continue
        seen.add(smiles)
        candidate_id = stable_candidate_id(cand.source_model, smiles)
        props = mol_props(mol)
        valid_rows.append(
            {
                "candidate_id": candidate_id,
                "target_id": target_id,
                "target_variant": target_variant,
                "pocket_id": pocket_id,
                "source_model": cand.source_model,
                "source_file": cand.source_file,
                "source_record": cand.source_record,
                "canonical_smiles": smiles,
                "valid_rdkit": True,
                "duplicate_removed": False,
                **props,
            }
        )

    writer = Chem.SDWriter(str(sdf_path))
    for row in valid_rows:
        mol = Chem.MolFromSmiles(row["canonical_smiles"])
        if mol is None:
            continue
        mol.SetProp("_Name", row["candidate_id"])
        for key, value in row.items():
            mol.SetProp(str(key), str(value))
        writer.write(mol)
    writer.close()

    csv_fields = [
        "candidate_id",
        "target_id",
        "target_variant",
        "pocket_id",
        "source_model",
        "source_file",
        "source_record",
        "canonical_smiles",
        "valid_rdkit",
    ]
    prop_fields = csv_fields + [
        "num_heavy_atoms",
        "num_atoms",
        "molecular_weight",
        "exact_mol_wt",
        "clogp",
        "tpsa",
        "qed",
        "hbd",
        "hba",
        "rotatable_bonds",
        "ring_count",
        "aromatic_ring_count",
        "formal_charge",
        "fraction_csp3",
    ]
    with candidates_csv.open("w", newline="", encoding="utf-8") as f:
        writer_csv = csv.DictWriter(f, fieldnames=csv_fields)
        writer_csv.writeheader()
        writer_csv.writerows({k: row[k] for k in csv_fields} for row in valid_rows)

    with props_csv.open("w", newline="", encoding="utf-8") as f:
        writer_csv = csv.DictWriter(f, fieldnames=prop_fields)
        writer_csv.writeheader()
        writer_csv.writerows({k: row[k] for k in prop_fields} for row in valid_rows)

    audit = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_molecule_count": len(candidates),
        "valid_unique_count": len(valid_rows),
        "invalid_count": len(invalid_rows),
        "duplicate_count": len(candidates) - len(valid_rows) - len(invalid_rows),
        "outputs": {
            "generated_egfr_candidates_sdf": str(sdf_path),
            "generated_egfr_candidates_csv": str(candidates_csv),
            "basic_properties_csv": str(props_csv),
        },
        "invalid_examples": invalid_rows[:20],
    }
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdf-dir", action="append", default=[], help="Directory or glob containing SDF files.")
    parser.add_argument("--sdf-file", action="append", default=[], help="Individual SDF file or glob.")
    parser.add_argument("--decompdiff-pt", action="append", default=[], help="DecompDiff result.pt file or glob.")
    parser.add_argument(
        "--out-prefix",
        default="results/generation/egfr_first_batch/generated_egfr_candidates",
        help="Output prefix. Writes .sdf and .csv beside basic_properties.csv.",
    )
    parser.add_argument("--target-id", default="EGFR")
    parser.add_argument("--target-variant", default="mixed")
    parser.add_argument("--pocket-id", default="EGFR-10A-mixed")
    args = parser.parse_args()

    candidates: list[Candidate] = []
    candidates.extend(load_sdf_candidates(args.sdf_dir, source_model="TargetDiff"))
    candidates.extend(load_sdf_candidates(args.sdf_file, source_model="SDF"))
    candidates.extend(load_decompdiff_pt_candidates(args.decompdiff_pt))

    if not candidates:
        raise SystemExit(
            "No generated molecules found. Provide --sdf-dir/--sdf-file or --decompdiff-pt."
        )

    audit = write_outputs(
        candidates,
        Path(args.out_prefix),
        target_id=args.target_id,
        target_variant=args.target_variant,
        pocket_id=args.pocket_id,
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
