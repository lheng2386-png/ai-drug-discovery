#!/usr/bin/env python3
"""Build a traceable EGFR known-ligand table from ChEMBL bioactivities."""

from __future__ import annotations

import csv
import gzip
import json
import re
import statistics
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem import Crippen, Descriptors, Lipinski, QED, rdMolDescriptors
from rdkit.Chem.MolStandardize import rdMolStandardize


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "ligands"
RAW_DIR = OUTPUT_DIR / "raw"
OUTPUT_CSV = OUTPUT_DIR / "egfr_known_ligands.csv"
AUDIT_JSON = OUTPUT_DIR / "egfr_known_ligands_audit.json"

BASE_URL = "https://www.ebi.ac.uk"
TARGET_CHEMBL_ID = "CHEMBL203"
PAGE_LIMIT = 1000
ALLOWED_TYPES = {"IC50", "Ki", "Kd"}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "egfr-ligand-curation/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def activity_url(offset: int = 0) -> str:
    params = {
        "target_chembl_id": TARGET_CHEMBL_ID,
        "target_organism": "Homo sapiens",
        "assay_type": "B",
        "standard_relation": "=",
        "standard_units": "nM",
        "pchembl_value__gte": "6",
        "data_validity_comment__isnull": "true",
        "potential_duplicate": "0",
        "limit": str(PAGE_LIMIT),
        "offset": str(offset),
    }
    return f"{BASE_URL}/chembl/api/data/activity.json?{urllib.parse.urlencode(params)}"


def largest_fragment(molecule: Chem.Mol) -> Chem.Mol:
    fragments = Chem.GetMolFrags(molecule, asMols=True, sanitizeFrags=True)
    return max(fragments, key=lambda mol: mol.GetNumHeavyAtoms())


def standardize_smiles(smiles: str) -> tuple[Chem.Mol, str, str]:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError("RDKit could not parse SMILES")
    molecule = rdMolStandardize.Cleanup(molecule)
    molecule = largest_fragment(molecule)
    uncharger = rdMolStandardize.Uncharger()
    molecule = uncharger.uncharge(molecule)
    canonical = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
    inchikey = Chem.MolToInchiKey(molecule)
    return molecule, canonical, inchikey


def normalize_mutation(value: str | None) -> str:
    if not value:
        return "unspecified"
    value = value.strip()
    if value.upper() == "UNDEFINED MUTATION":
        return "undefined"
    mutations = [item.strip() for item in value.split(",") if item.strip()]

    def mutation_key(mutation: str) -> tuple[int, str]:
        match = re.search(r"(\d+)", mutation)
        return (int(match.group(1)) if match else 10**9, mutation)

    return ",".join(sorted(set(mutations), key=mutation_key))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).isoformat()

    activities: list[dict] = []
    offset = 0
    total_count = None
    while total_count is None or offset < total_count:
        payload = fetch_json(activity_url(offset))
        if total_count is None:
            total_count = int(payload["page_meta"]["total_count"])
        page = payload.get("activities", [])
        activities.extend(page)
        offset += len(page)
        print(f"Downloaded {len(activities)}/{total_count} ChEMBL activity records")
        if not page:
            break

    raw_path = RAW_DIR / "chembl203_binding_activities.jsonl.gz"
    with gzip.open(raw_path, "wt", encoding="utf-8") as handle:
        for activity in activities:
            handle.write(json.dumps(activity, ensure_ascii=False) + "\n")

    filtered = [
        activity
        for activity in activities
        if activity.get("standard_type") in ALLOWED_TYPES
        and activity.get("standard_value") not in (None, "")
        and activity.get("canonical_smiles")
        and activity.get("molecule_chembl_id")
    ]

    standardized = []
    invalid_smiles = 0
    smiles_cache: dict[str, tuple[Chem.Mol, str, str]] = {}
    for activity in filtered:
        source_smiles = activity["canonical_smiles"]
        try:
            if source_smiles not in smiles_cache:
                smiles_cache[source_smiles] = standardize_smiles(source_smiles)
            molecule, canonical_smiles, inchikey = smiles_cache[source_smiles]
        except (ValueError, RuntimeError):
            invalid_smiles += 1
            continue
        record = dict(activity)
        record["_molecule"] = molecule
        record["_canonical_smiles"] = canonical_smiles
        record["_inchikey"] = inchikey
        record["_normalized_mutation"] = normalize_mutation(
            activity.get("assay_variant_mutation")
        )
        standardized.append(record)

    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for activity in standardized:
        groups[
            (
                activity["_inchikey"],
                activity["_normalized_mutation"],
                activity["standard_type"],
            )
        ].append(activity)

    rows = []
    for (inchikey, mutation, activity_type), records in groups.items():
        best = max(records, key=lambda record: float(record["pchembl_value"]))
        molecule = best["_molecule"]
        canonical_smiles = best["_canonical_smiles"]
        molecule_ids = sorted({record["molecule_chembl_id"] for record in records})
        molecule_id = best["molecule_chembl_id"]

        values = [float(record["standard_value"]) for record in records]
        pchembl_values = [float(record["pchembl_value"]) for record in records]
        documents = sorted(
            {record["document_chembl_id"] for record in records if record.get("document_chembl_id")}
        )
        assays = sorted(
            {record["assay_chembl_id"] for record in records if record.get("assay_chembl_id")}
        )
        rows.append(
            {
                "target_id": "EGFR",
                "target_chembl_id": TARGET_CHEMBL_ID,
                "uniprot_id": "P00533",
                "assay_variant_mutation": mutation,
                "molecule_chembl_id": molecule_id,
                "all_molecule_chembl_ids": ";".join(molecule_ids),
                "parent_molecule_chembl_id": best.get("parent_molecule_chembl_id") or "",
                "molecule_pref_name": best.get("molecule_pref_name") or "",
                "canonical_smiles": canonical_smiles,
                "inchikey": inchikey,
                "activity_type": activity_type,
                "best_value_nm": min(values),
                "median_value_nm": statistics.median(values),
                "max_pchembl_value": max(pchembl_values),
                "measurement_count": len(records),
                "assay_chembl_ids": ";".join(assays),
                "document_chembl_ids": ";".join(documents),
                "molecular_weight": round(Descriptors.MolWt(molecule), 3),
                "clogp": round(Crippen.MolLogP(molecule), 3),
                "tpsa": round(rdMolDescriptors.CalcTPSA(molecule), 3),
                "hbd": Lipinski.NumHDonors(molecule),
                "hba": Lipinski.NumHAcceptors(molecule),
                "rotatable_bonds": Lipinski.NumRotatableBonds(molecule),
                "qed": round(QED.qed(molecule), 4),
                "source": "ChEMBL",
                "source_url": (
                    f"https://www.ebi.ac.uk/chembl/explore/compound/{molecule_id}"
                ),
                "retrieved_at": retrieved_at,
            }
        )

    rows.sort(
        key=lambda row: (
            row["assay_variant_mutation"],
            row["activity_type"],
            -float(row["max_pchembl_value"]),
            row["molecule_chembl_id"],
        )
    )
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    audit = {
        "retrieved_at": retrieved_at,
        "source": "ChEMBL web services",
        "target_chembl_id": TARGET_CHEMBL_ID,
        "query": activity_url(0),
        "filters": {
            "target_organism": "Homo sapiens",
            "assay_type": "B",
            "standard_relation": "=",
            "standard_units": "nM",
            "pchembl_value_min": 6,
            "data_validity_comment": None,
            "potential_duplicate": 0,
            "allowed_standard_types": sorted(ALLOWED_TYPES),
        },
        "downloaded_activity_count": len(activities),
        "retained_activity_count": len(filtered),
        "aggregated_row_count": len(rows),
        "unique_chemical_identity_count": len({row["inchikey"] for row in rows}),
        "invalid_smiles_count": invalid_smiles,
        "rdkit_version": rdBase.rdkitVersion,
        "aggregation": (
            "one row per standardized InChIKey, normalized assay mutation set, "
            "and activity type; "
            "best and median exact nM measurements retained"
        ),
    }
    AUDIT_JSON.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
