"""Validate the fixed PLINDER v0.1 sample without modifying source data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from Bio import SeqIO
from Bio.PDB import PDBParser
from rdkit import Chem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    return parser.parse_args()


def main() -> int:
    root = parse_args().project_root.resolve()
    data_root = root / "data/raw/plinder/2024-04-v1"
    manifest = pd.read_csv(root / "data/sample-structures-v0.1.csv")
    annotations = pd.read_parquet(
        data_root / "annotation_table_nonredundant.parquet",
        columns=[
            "system_id",
            "ligand_rdkit_canonical_smiles",
            "ligand_num_heavy_atoms",
            "system_num_pocket_residues",
            "ligand_num_interacting_residues",
        ],
    ).set_index("system_id")
    parser = PDBParser(QUIET=True)
    rows: list[dict[str, object]] = []

    for record in manifest.itertuples(index=False):
        system_dir = data_root / "sample-systems-v0.1" / record.system_id
        sdf_path = next((system_dir / "ligand_files").glob("*.sdf"))
        molecule = Chem.MolFromMolFile(
            str(sdf_path), sanitize=True, removeHs=False
        )
        sanitize_ok = molecule is not None
        molecule_no_h = Chem.RemoveHs(molecule) if molecule else None
        canonical = (
            Chem.MolToSmiles(
                molecule_no_h, canonical=True, isomericSmiles=True
            )
            if molecule_no_h
            else None
        )
        metadata_smiles = annotations.loc[
            record.system_id, "ligand_rdkit_canonical_smiles"
        ]
        metadata_molecule = Chem.MolFromSmiles(metadata_smiles)
        metadata_canonical = (
            Chem.MolToSmiles(
                metadata_molecule, canonical=True, isomericSmiles=True
            )
            if metadata_molecule
            else None
        )
        smiles_match = canonical == metadata_canonical
        heavy_atoms = molecule.GetNumHeavyAtoms() if molecule else None
        expected_heavy_atoms = int(
            annotations.loc[record.system_id, "ligand_num_heavy_atoms"]
        )

        ligand_coordinates = np.empty((0, 3))
        if molecule:
            conformer = molecule.GetConformer()
            ligand_coordinates = np.asarray(
                [
                    list(conformer.GetAtomPosition(index))
                    for index, atom in enumerate(molecule.GetAtoms())
                    if atom.GetAtomicNum() > 1
                ]
            )

        structure = parser.get_structure(
            record.system_id, str(system_dir / "receptor.pdb")
        )
        protein_residues = []
        pocket_residues = []
        for residue in structure.get_residues():
            if residue.id[0] != " ":
                continue
            protein_residues.append(residue)
            residue_coordinates = np.asarray(
                [
                    atom.coord
                    for atom in residue.get_atoms()
                    if atom.element != "H"
                ]
            )
            if len(residue_coordinates) == 0:
                continue
            distances = np.linalg.norm(
                residue_coordinates[:, None, :]
                - ligand_coordinates[None, :, :],
                axis=2,
            )
            if float(np.min(distances)) <= 6.0:
                pocket_residues.append(residue)

        fasta_records = list(
            SeqIO.parse(system_dir / "sequences.fasta", "fasta")
        )
        chain_mapping = json.loads(
            (system_dir / "chain_mapping.json").read_text()
        )
        rows.append(
            {
                "system_id": record.system_id,
                "split": record.split,
                "sanitize_ok": sanitize_ok,
                "smiles_match": smiles_match,
                "sdf_canonical_smiles": canonical,
                "metadata_canonical_smiles": metadata_canonical,
                "heavy_atoms": heavy_atoms,
                "expected_heavy_atoms": expected_heavy_atoms,
                "fasta_records": len(fasta_records),
                "fasta_length": sum(
                    len(fasta_record.seq)
                    for fasta_record in fasta_records
                ),
                "pdb_residues": len(protein_residues),
                "chain_mapping_entries": len(chain_mapping),
                "pocket_6A_residues": len(pocket_residues),
                "metadata_pocket_residues": int(
                    annotations.loc[
                        record.system_id, "system_num_pocket_residues"
                    ]
                ),
                "metadata_interacting_residues": int(
                    annotations.loc[
                        record.system_id,
                        "ligand_num_interacting_residues",
                    ]
                ),
            }
        )

    results = pd.DataFrame(rows)
    print(results.to_string(index=False))
    print("\nSUMMARY")
    print(f"sanitize: {int(results.sanitize_ok.sum())}/{len(results)}")
    print(
        "SMILES chemistry match: "
        f"{int(results.smiles_match.sum())}/{len(results)}"
    )
    print(
        "heavy atom match: "
        f"{int((results.heavy_atoms == results.expected_heavy_atoms).sum())}"
        f"/{len(results)}"
    )
    print(
        "single FASTA record: "
        f"{int((results.fasta_records == 1).sum())}/{len(results)}"
    )
    print(
        "nonempty 6A pocket: "
        f"{int((results.pocket_6A_residues > 0).sum())}/{len(results)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
