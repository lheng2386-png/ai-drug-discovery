"""Build auditable full-protein and pocket-level inputs for the fixed sample."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from Bio import Align, SeqIO
from Bio.PDB import PDBParser
from Bio.PDB.Polypeptide import protein_letters_3to1
from rdkit import Chem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/sample-model-inputs-v0.1.csv"),
    )
    return parser.parse_args()


def parse_residue_labels(value: str) -> list[tuple[str, int, int]]:
    labels = []
    if not value:
        return labels
    for item in value.split(";"):
        chain, structure_number, sequence_index = item.rsplit("_", 2)
        labels.append((chain, int(structure_number), int(sequence_index)))
    return labels


def protein_residues(structure) -> list:
    return [
        residue
        for residue in structure.get_residues()
        if residue.id[0] == " "
        and residue.resname.upper() in protein_letters_3to1
    ]


def align_structure_to_fasta(
    residues: list, fasta_sequence: str
) -> tuple[dict[int, int], float]:
    structure_sequence = "".join(
        protein_letters_3to1[residue.resname.upper()] for residue in residues
    )
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -5
    aligner.extend_gap_score = -0.5
    alignment = aligner.align(structure_sequence, fasta_sequence)[0]
    mapping: dict[int, int] = {}
    matches = 0
    mapped = 0
    for structure_block, fasta_block in zip(
        alignment.aligned[0], alignment.aligned[1]
    ):
        structure_start, structure_end = map(int, structure_block)
        fasta_start, fasta_end = map(int, fasta_block)
        block_length = min(
            structure_end - structure_start, fasta_end - fasta_start
        )
        for offset in range(block_length):
            structure_index = structure_start + offset
            fasta_index = fasta_start + offset
            residue_number = int(residues[structure_index].id[1])
            mapping[residue_number] = fasta_index
            mapped += 1
            if structure_sequence[structure_index] == fasta_sequence[fasta_index]:
                matches += 1
    identity = matches / mapped if mapped else 0.0
    return mapping, identity


def serialize_indices(indices: list[int], sequence: str) -> str:
    return ";".join(f"{index}:{sequence[index]}" for index in sorted(set(indices)))


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    output = args.output
    if not output.is_absolute():
        output = root / output
    data_root = root / "data/raw/plinder/2024-04-v1"
    manifest = pd.read_csv(root / "data/sample-structures-v0.1.csv")
    annotations = pd.read_parquet(
        data_root / "annotation_table_nonredundant.parquet",
        columns=[
            "system_id",
            "ligand_interacting_residues",
            "ligand_neighboring_residues",
        ],
    ).set_index("system_id")
    parser = PDBParser(QUIET=True)
    output_rows = []

    for record in manifest.itertuples(index=False):
        system_dir = data_root / "sample-systems-v0.1" / record.system_id
        fasta_records = list(
            SeqIO.parse(system_dir / "sequences.fasta", "fasta")
        )
        if len(fasta_records) != 1:
            raise ValueError(
                f"{record.system_id}: expected one FASTA record, "
                f"found {len(fasta_records)}"
            )
        fasta_record = fasta_records[0]
        fasta_sequence = str(fasta_record.seq)
        source_chain = fasta_record.id
        chain_mapping = json.loads(
            (system_dir / "chain_mapping.json").read_text()
        )
        receptor_chain = chain_mapping[source_chain]

        structure = parser.get_structure(
            record.system_id, str(system_dir / "receptor.pdb")
        )
        chain = next(
            candidate
            for candidate in structure.get_chains()
            if candidate.id == receptor_chain
        )
        residues = protein_residues(chain)
        residue_to_sequence, alignment_identity = align_structure_to_fasta(
            residues, fasta_sequence
        )

        sdf_path = next((system_dir / "ligand_files").glob("*.sdf"))
        molecule = Chem.MolFromMolFile(
            str(sdf_path), sanitize=True, removeHs=False
        )
        if molecule is None:
            raise ValueError(f"{record.system_id}: ligand sanitize failed")
        conformer = molecule.GetConformer()
        ligand_coordinates = np.asarray(
            [
                list(conformer.GetAtomPosition(index))
                for index, atom in enumerate(molecule.GetAtoms())
                if atom.GetAtomicNum() > 1
            ]
        )
        pocket_6a_indices = []
        for residue in residues:
            coordinates = np.asarray(
                [
                    atom.coord
                    for atom in residue.get_atoms()
                    if atom.element != "H"
                ]
            )
            if not len(coordinates):
                continue
            minimum_distance = np.min(
                np.linalg.norm(
                    coordinates[:, None, :]
                    - ligand_coordinates[None, :, :],
                    axis=2,
                )
            )
            residue_number = int(residue.id[1])
            if minimum_distance <= 6.0 and residue_number in residue_to_sequence:
                pocket_6a_indices.append(
                    residue_to_sequence[residue_number]
                )

        interacting_labels = parse_residue_labels(
            annotations.loc[
                record.system_id, "ligand_interacting_residues"
            ]
        )
        neighboring_labels = parse_residue_labels(
            annotations.loc[
                record.system_id, "ligand_neighboring_residues"
            ]
        )
        official_interacting = [
            residue_to_sequence[structure_number]
            for chain_id, structure_number, _ in interacting_labels
            if chain_id == source_chain
            and structure_number in residue_to_sequence
        ]
        official_neighboring = [
            residue_to_sequence[structure_number]
            for chain_id, structure_number, _ in neighboring_labels
            if chain_id == source_chain
            and structure_number in residue_to_sequence
        ]
        external_neighboring = [
            f"{chain_id}_{structure_number}_{sequence_index}"
            for chain_id, structure_number, sequence_index in neighboring_labels
            if chain_id != source_chain
        ]
        all_indices = (
            official_interacting + official_neighboring + pocket_6a_indices
        )
        if any(index < 0 or index >= len(fasta_sequence) for index in all_indices):
            raise ValueError(f"{record.system_id}: sequence index out of range")

        output_rows.append(
            {
                "system_id": record.system_id,
                "split": record.split,
                "source_chain": source_chain,
                "receptor_chain": receptor_chain,
                "full_sequence": fasta_sequence,
                "full_sequence_length": len(fasta_sequence),
                "structure_residue_count": len(residues),
                "structure_fasta_alignment_identity": alignment_identity,
                "official_interacting_residues": serialize_indices(
                    official_interacting, fasta_sequence
                ),
                "official_interacting_count": len(official_interacting),
                "official_neighboring_residues": serialize_indices(
                    official_neighboring, fasta_sequence
                ),
                "official_neighboring_count": len(official_neighboring),
                "external_neighboring_residues": ";".join(external_neighboring),
                "external_neighboring_count": len(external_neighboring),
                "pocket_6a_residues": serialize_indices(
                    pocket_6a_indices, fasta_sequence
                ),
                "pocket_6a_count": len(pocket_6a_indices),
                "ligand_sdf": str(sdf_path.relative_to(root)),
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(output_rows)
    result.to_csv(output, index=False)
    print(result.drop(columns=["full_sequence"]).to_string(index=False))
    print(f"\nWrote {len(result)} rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
