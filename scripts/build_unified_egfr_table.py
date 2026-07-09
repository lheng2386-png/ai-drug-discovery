#!/usr/bin/env python3
"""Build the first unified EGFR target-conditioned candidate table.

The table is intentionally target-conditioned: one row represents one
``(target condition / pocket, molecule candidate)`` pair. Ligand-only
properties such as QED and ADMET predictions are repeated across EGFR variants,
while PLI, docking, selectivity, and Pareto fields are target-specific slots
that will be filled by later experiments.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

POCKET_MANIFEST = ROOT / "data/pockets/egfr/egfr_pocket_manifest.csv"
STRUCTURE_MANIFEST = ROOT / "data/targets/egfr/egfr_structure_manifest.csv"
KNOWN_LIGANDS = ROOT / "data/ligands/egfr_known_ligands.csv"
EVALUATION_SMOKE = ROOT / "results/evaluation/egfr_known_ligands_smoke.csv"

OUT_DIR = ROOT / "data/unified"
OUT_CSV = OUT_DIR / "egfr_known_ligands_unified_v0.1.csv"
OUT_AUDIT = OUT_DIR / "egfr_known_ligands_unified_v0.1.audit.json"


TARGET_CONDITIONAL_COLUMNS = [
    "record_id",
    "target_id",
    "target_chembl_id",
    "uniprot_id",
    "target_variant",
    "expected_mutations",
    "pdb_id",
    "protein_chain",
    "structure_path",
    "structure_resolution_angstrom",
    "structure_role",
    "pocket_id",
    "pocket_path",
    "pocket_radius_angstrom",
    "pocket_residue_count",
    "pocket_atom_count",
    "reference_ligand_resname",
    "reference_ligand_file",
    "reference_ligand_covalent",
    "candidate_id",
    "candidate_source",
    "generation_model",
    "generation_run_id",
    "molecule_chembl_id",
    "molecule_pref_name",
    "canonical_smiles",
    "inchikey",
    "experimental_assay_variant_mutation",
    "experimental_activity_type",
    "experimental_best_value_nm",
    "experimental_median_value_nm",
    "experimental_max_pchembl_value",
    "experimental_measurement_count",
    "known_ligand_source_url",
    "qed_rdkit",
    "molecular_weight_rdkit",
    "clogp_rdkit",
    "tpsa_chembl",
    "hbd_chembl",
    "hba_chembl",
    "rotatable_bonds_chembl",
    "sa_score",
    "sa_score_method",
    "pli_score",
    "pli_model",
    "pli_embedding_pair_id",
    "docking_score_vina_kcal_mol",
    "docking_pose_path",
    "docking_structure_id",
    "docking_validated_redocking",
    "toxicity_flag",
    "admet_summary_flag",
    "diversity_cluster_id",
    "diversity_nearest_neighbor_tanimoto",
    "novelty_reference_dataset",
    "novelty_max_train_similarity",
    "pareto_rank",
    "pareto_selected",
    "feedback_label",
    "feedback_weight",
    "provenance_created_at",
    "provenance_notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(*parts: str) -> str:
    text = "|".join(parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def first_by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if value and value not in out:
            out[value] = row
    return out


def choose_10a_pockets(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    chosen = [row for row in rows if row.get("radius_angstrom") in {"10", "10.0"}]
    chosen.sort(key=lambda r: (r["variant"], r["pdb_id"]))
    return chosen


def toxicity_flag_from_admet(eval_row: dict[str, str]) -> str:
    """Conservative smoke-test flag from ADMET-AI probability-like fields.

    This is only a triage flag, not a toxicity claim. A blank value means no
    high-risk signal under the current simple thresholds.
    """

    high_risk_fields = {
        "admet_ai_AMES": 0.70,
        "admet_ai_Carcinogens_Lagunin": 0.70,
        "admet_ai_ClinTox": 0.70,
        "admet_ai_DILI": 0.70,
        "admet_ai_hERG": 0.70,
        "admet_ai_Skin_Reaction": 0.70,
    }
    hits: list[str] = []
    for field, threshold in high_risk_fields.items():
        raw = eval_row.get(field, "")
        if raw == "":
            continue
        try:
            if float(raw) >= threshold:
                hits.append(field.removeprefix("admet_ai_"))
        except ValueError:
            continue
    return ";".join(hits)


def admet_summary_flag(eval_row: dict[str, str]) -> str:
    flags = []
    toxicity = toxicity_flag_from_admet(eval_row)
    if toxicity:
        flags.append(f"toxicity_screen:{toxicity}")
    if eval_row.get("admet_ai_PAINS_alert") not in {"", "0", "0.0"}:
        flags.append("PAINS")
    if eval_row.get("admet_ai_BRENK_alert") not in {"", "0", "0.0"}:
        flags.append("BRENK")
    if eval_row.get("admet_ai_NIH_alert") not in {"", "0", "0.0"}:
        flags.append("NIH")
    return ";".join(flags)


def main() -> None:
    pockets = choose_10a_pockets(read_csv(POCKET_MANIFEST))
    structures = first_by_key(read_csv(STRUCTURE_MANIFEST), "pdb_id")
    known_by_chembl = first_by_key(read_csv(KNOWN_LIGANDS), "molecule_chembl_id")
    evaluation_rows = read_csv(EVALUATION_SMOKE)

    evaluation_by_chembl = first_by_key(evaluation_rows, "molecule_chembl_id")
    eval_passthrough_columns = [
        col
        for col in (evaluation_rows[0].keys() if evaluation_rows else [])
        if col.startswith("posebusters_") or col.startswith("admet_ai_")
    ]

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows: list[dict[str, str]] = []

    for pocket in pockets:
        structure = structures[pocket["pdb_id"]]
        for eval_row in evaluation_rows:
            chembl_id = eval_row["molecule_chembl_id"]
            known = known_by_chembl.get(chembl_id, {})
            variant = pocket["variant"]
            pdb_id = pocket["pdb_id"]
            candidate_id = f"known-egfr-{chembl_id}"
            pocket_id = f"EGFR-{variant}-{pdb_id}-10A"
            record_id = "egfr_" + stable_id(variant, pdb_id, chembl_id)

            row = {
                "record_id": record_id,
                "target_id": pocket["target_id"],
                "target_chembl_id": known.get("target_chembl_id", "CHEMBL203"),
                "uniprot_id": known.get("uniprot_id", structure.get("uniprot_id", "P00533")),
                "target_variant": variant,
                "expected_mutations": structure.get("expected_mutations", ""),
                "pdb_id": pdb_id,
                "protein_chain": pocket["protein_chain"],
                "structure_path": f"data/targets/egfr/structures/{pdb_id}.pdb",
                "structure_resolution_angstrom": structure.get("resolution_angstrom", ""),
                "structure_role": structure.get("role", ""),
                "pocket_id": pocket_id,
                "pocket_path": f"data/pockets/egfr/{pocket['pocket_file']}",
                "pocket_radius_angstrom": pocket["radius_angstrom"],
                "pocket_residue_count": pocket["pocket_residue_count"],
                "pocket_atom_count": pocket["pocket_atom_count"],
                "reference_ligand_resname": pocket["ligand_resname"],
                "reference_ligand_file": pocket["ligand_file"],
                "reference_ligand_covalent": pocket["covalent_ligand"],
                "candidate_id": candidate_id,
                "candidate_source": "known_ligand_seed",
                "generation_model": "none",
                "generation_run_id": "egfr_known_ligands_smoke_v0.1",
                "molecule_chembl_id": chembl_id,
                "molecule_pref_name": eval_row.get("molecule_pref_name", known.get("molecule_pref_name", "")),
                "canonical_smiles": eval_row.get("canonical_smiles", known.get("canonical_smiles", "")),
                "inchikey": known.get("inchikey", ""),
                "experimental_assay_variant_mutation": known.get("assay_variant_mutation", ""),
                "experimental_activity_type": known.get("activity_type", ""),
                "experimental_best_value_nm": known.get("best_value_nm", ""),
                "experimental_median_value_nm": known.get("median_value_nm", ""),
                "experimental_max_pchembl_value": known.get("max_pchembl_value", ""),
                "experimental_measurement_count": known.get("measurement_count", ""),
                "known_ligand_source_url": known.get("source_url", ""),
                "qed_rdkit": eval_row.get("qed_rdkit", ""),
                "molecular_weight_rdkit": eval_row.get("molecular_weight_rdkit", ""),
                "clogp_rdkit": eval_row.get("clogp_rdkit", ""),
                "tpsa_chembl": known.get("tpsa", ""),
                "hbd_chembl": known.get("hbd", ""),
                "hba_chembl": known.get("hba", ""),
                "rotatable_bonds_chembl": known.get("rotatable_bonds", ""),
                "sa_score": "",
                "sa_score_method": "pending",
                "pli_score": "",
                "pli_model": "pending",
                "pli_embedding_pair_id": "",
                "docking_score_vina_kcal_mol": "",
                "docking_pose_path": "",
                "docking_structure_id": "",
                "docking_validated_redocking": "false",
                "toxicity_flag": toxicity_flag_from_admet(eval_row),
                "admet_summary_flag": admet_summary_flag(eval_row),
                "diversity_cluster_id": "",
                "diversity_nearest_neighbor_tanimoto": "",
                "novelty_reference_dataset": "pending",
                "novelty_max_train_similarity": "",
                "pareto_rank": "",
                "pareto_selected": "",
                "feedback_label": "",
                "feedback_weight": "",
                "provenance_created_at": created_at,
                "provenance_notes": "Seed table before generated molecules; ADMET/PoseBusters are ligand-only smoke-test predictions.",
            }
            for col in eval_passthrough_columns:
                row[col] = eval_row.get(col, "")
            rows.append(row)

    fieldnames = TARGET_CONDITIONAL_COLUMNS + eval_passthrough_columns
    write_csv(OUT_CSV, rows, fieldnames)

    unique_variants = sorted({row["target_variant"] for row in rows})
    unique_molecules = sorted({row["molecule_chembl_id"] for row in rows})
    audit = {
        "created_at": created_at,
        "script": str(Path("scripts/build_unified_egfr_table.py")),
        "output_csv": str(OUT_CSV.relative_to(ROOT)),
        "row_count": len(rows),
        "column_count": len(fieldnames),
        "target_condition_count": len(pockets),
        "molecule_count": len(unique_molecules),
        "target_variants": unique_variants,
        "molecule_chembl_ids": unique_molecules,
        "source_files": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in [POCKET_MANIFEST, STRUCTURE_MANIFEST, KNOWN_LIGANDS, EVALUATION_SMOKE]
        },
        "output_sha256": sha256_file(OUT_CSV),
        "design_note": "One row equals one target-conditioned candidate: EGFR pocket condition x molecule.",
        "pending_fields": [
            "sa_score",
            "pli_score",
            "docking_score_vina_kcal_mol",
            "diversity_cluster_id",
            "novelty_max_train_similarity",
            "pareto_rank",
        ],
    }
    OUT_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
