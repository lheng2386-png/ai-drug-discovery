#!/usr/bin/env python3
"""Run a small, reproducible ligand-quality and ADMET prediction smoke test."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from admet_ai import ADMETModel
from posebusters import PoseBusters
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, Descriptors, QED


DEFAULT_NAMES = [
    "ERLOTINIB",
    "GEFITINIB",
    "AFATINIB",
    "OSIMERTINIB",
    "LAPATINIB",
    "NERATINIB",
    "VANDETANIB",
    "ABIVERTINIB",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/ligands/egfr_known_ligands.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/evaluation/egfr_known_ligands_smoke.csv"),
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=Path("data/egfr-evaluation-smoke-audit.json"),
    )
    return parser.parse_args()


def select_ligands(path: Path) -> pd.DataFrame:
    table = pd.read_csv(path)
    selected = (
        table[table["molecule_pref_name"].isin(DEFAULT_NAMES)]
        .sort_values(["molecule_pref_name", "best_value_nm"])
        .drop_duplicates("molecule_pref_name")
        .set_index("molecule_pref_name")
        .loc[DEFAULT_NAMES]
        .reset_index()
    )
    return selected[["molecule_pref_name", "molecule_chembl_id", "canonical_smiles"]]


def build_3d_molecules(table: pd.DataFrame) -> tuple[list[Chem.Mol], list[dict]]:
    molecules: list[Chem.Mol] = []
    descriptors: list[dict] = []
    for row in table.itertuples(index=False):
        mol = Chem.MolFromSmiles(row.canonical_smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES for {row.molecule_pref_name}")
        descriptors.append(
            {
                "molecule_pref_name": row.molecule_pref_name,
                "molecule_chembl_id": row.molecule_chembl_id,
                "canonical_smiles": row.canonical_smiles,
                "molecular_weight_rdkit": Descriptors.MolWt(mol),
                "clogp_rdkit": Descriptors.MolLogP(mol),
                "qed_rdkit": QED.qed(mol),
            }
        )
        mol_3d = Chem.AddHs(mol)
        status = AllChem.EmbedMolecule(mol_3d, randomSeed=20260709)
        if status != 0:
            raise RuntimeError(f"3D embedding failed for {row.molecule_pref_name}")
        AllChem.MMFFOptimizeMolecule(mol_3d, maxIters=500)
        mol_3d.SetProp("_Name", row.molecule_pref_name)
        molecules.append(mol_3d)
    return molecules, descriptors


def main() -> None:
    args = parse_args()
    selected = select_ligands(args.input)
    molecules, descriptors = build_3d_molecules(selected)

    pose_report = PoseBusters(config="mol", max_workers=0).bust(
        molecules, full_report=True
    )
    pose_report = pose_report.reset_index(drop=True)
    pose_report.columns = [
        "posebusters_" + "_".join(str(part) for part in col if str(part))
        if isinstance(col, tuple)
        else f"posebusters_{col}"
        for col in pose_report.columns
    ]

    model = ADMETModel()
    admet = model.predict(selected["canonical_smiles"].tolist()).reset_index(drop=True)
    admet.columns = [f"admet_ai_{column}" for column in admet.columns]

    result = pd.concat(
        [pd.DataFrame(descriptors), pose_report, admet],
        axis=1,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)

    audit = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": str(args.input),
        "output": str(args.output),
        "molecule_count": len(result),
        "molecule_names": DEFAULT_NAMES,
        "rdkit_version": rdBase.rdkitVersion,
        "random_seed": 20260709,
        "posebusters_config": "mol",
        "admet_ai_version": "2.0.1",
        "important_limitations": [
            "ADMET-AI outputs are model predictions, not experimental measurements.",
            "PoseBusters mol checks test molecular plausibility, not protein binding.",
            "This smoke test does not run docking or estimate binding affinity.",
        ],
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

