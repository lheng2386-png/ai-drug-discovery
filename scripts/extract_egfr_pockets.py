#!/usr/bin/env python3
"""Extract reproducible ligand-centred EGFR pockets from selected PDB files."""

from __future__ import annotations

import csv
import math
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRUCTURE_DIR = ROOT / "data" / "targets" / "egfr" / "structures"
OUTPUT_DIR = ROOT / "data" / "pockets" / "egfr"
RADII_ANGSTROM = (6.0, 10.0)

SELECTIONS = [
    ("4G5J", "WT", "0WN", "A", 1101, True),
    ("2ITZ", "L858R", "IRE", "A", 2021, False),
    ("2JIU", "T790M", "AEE", "A", 2017, False),
    ("7VRA", "T790M/C797S", "I0A", "A", 1101, False),
]


def parse_xyz(line: str) -> tuple[float, float, float]:
    return float(line[30:38]), float(line[38:46]), float(line[46:54])


def squared_distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def extract(
    source: Path,
    ligand_name: str,
    ligand_chain: str,
    ligand_resseq: int,
    pocket_path: Path,
    ligand_path: Path,
    radius_angstrom: float,
) -> tuple[int, int, str]:
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    ligand_lines = [
        line
        for line in lines
        if line.startswith("HETATM")
        and line[17:20].strip() == ligand_name
        and line[21].strip() == ligand_chain
        and int(line[22:26]) == ligand_resseq
        and line[76:78].strip().upper() != "H"
    ]
    if not ligand_lines:
        raise RuntimeError(f"Ligand {ligand_name} {ligand_chain} {ligand_resseq} not found in {source}")

    ligand_xyz = [parse_xyz(line) for line in ligand_lines]
    protein_atom_lines = [line for line in lines if line.startswith("ATOM  ")]
    selected_residues: set[tuple[str, int, str]] = set()
    radius_squared = radius_angstrom**2

    for line in protein_atom_lines:
        xyz = parse_xyz(line)
        if any(squared_distance(xyz, ligand_atom) <= radius_squared for ligand_atom in ligand_xyz):
            selected_residues.add((line[21], int(line[22:26]), line[26]))

    selected_atom_lines = [
        line
        for line in protein_atom_lines
        if (line[21], int(line[22:26]), line[26]) in selected_residues
    ]
    if not selected_atom_lines:
        raise RuntimeError(f"No protein atoms selected for {source}")

    pocket_path.parent.mkdir(parents=True, exist_ok=True)
    pocket_path.write_text("".join(selected_atom_lines) + "END\n", encoding="utf-8")
    ligand_path.write_text("".join(ligand_lines) + "END\n", encoding="utf-8")
    residue_ids = ";".join(
        f"{chain}:{resseq}{icode.strip()}" for chain, resseq, icode in sorted(selected_residues)
    )
    return len(selected_residues), len(selected_atom_lines), residue_ids


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for pdb_id, variant, ligand, chain, resseq, covalent in SELECTIONS:
        ligand_path = OUTPUT_DIR / f"{pdb_id}_{ligand}_ligand.pdb"
        for radius_angstrom in RADII_ANGSTROM:
            radius_label = f"{int(radius_angstrom)}A"
            pocket_path = OUTPUT_DIR / (
                f"{pdb_id}_{variant.replace('/', '-')}_pocket_{radius_label}.pdb"
            )
            residue_count, atom_count, residue_ids = extract(
                STRUCTURE_DIR / f"{pdb_id}.pdb",
                ligand,
                chain,
                resseq,
                pocket_path,
                ligand_path,
                radius_angstrom,
            )
            rows.append(
                {
                    "target_id": "EGFR",
                    "variant": variant,
                    "pdb_id": pdb_id,
                    "protein_chain": chain,
                    "ligand_resname": ligand,
                    "ligand_chain": chain,
                    "ligand_resseq": resseq,
                    "covalent_ligand": str(covalent).lower(),
                    "radius_angstrom": radius_angstrom,
                    "pocket_residue_count": residue_count,
                    "pocket_atom_count": atom_count,
                    "pocket_file": pocket_path.name,
                    "ligand_file": ligand_path.name,
                    "pocket_residues": residue_ids,
                }
            )

    manifest = OUTPUT_DIR / "egfr_pocket_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    shutil.copyfile(
        OUTPUT_DIR / "4G5J_WT_pocket_6A.pdb",
        ROOT / "data" / "pockets" / "egfr_pocket.pdb",
    )
    print(f"Wrote {len(rows)} pockets and {manifest}")


if __name__ == "__main__":
    main()
