#!/usr/bin/env python3
"""Download the first reproducible EGFR target data bundle.

Sources are restricted to UniProt, AlphaFold DB, and RCSB PDB. Coordinate
files are treated as reproducible local data and are excluded from Git.
"""

from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "data" / "targets" / "egfr"
SEQUENCE_DIR = TARGET_DIR / "sequences"
STRUCTURE_DIR = TARGET_DIR / "structures"
METADATA_DIR = TARGET_DIR / "metadata"

UNIPROT_ID = "P00533"
PDB_SELECTIONS = [
    {
        "pdb_id": "4G5J",
        "variant": "WT",
        "expected_mutations": "",
        "role": "wild-type reference; covalent afatinib complex",
    },
    {
        "pdb_id": "2ITZ",
        "variant": "L858R",
        "expected_mutations": "L858R",
        "role": "activating-mutant reference; gefitinib complex",
    },
    {
        "pdb_id": "2JIU",
        "variant": "T790M",
        "expected_mutations": "T790M",
        "role": "resistance-mutant reference; AEE788 complex",
    },
    {
        "pdb_id": "7VRA",
        "variant": "T790M/C797S",
        "expected_mutations": "T790M;C797S",
        "role": "C797S-containing reference; HC5476 complex",
    },
]


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "egfr-research-data/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    for directory in (SEQUENCE_DIR, STRUCTURE_DIR, METADATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    retrieved_at = datetime.now(timezone.utc).isoformat()

    uniprot_fasta = SEQUENCE_DIR / f"{UNIPROT_ID}.fasta"
    uniprot_json = METADATA_DIR / f"uniprot_{UNIPROT_ID}.json"
    download(f"https://rest.uniprot.org/uniprotkb/{UNIPROT_ID}.fasta", uniprot_fasta)
    download(f"https://rest.uniprot.org/uniprotkb/{UNIPROT_ID}.json", uniprot_json)

    alphafold_api = METADATA_DIR / f"alphafold_{UNIPROT_ID}.json"
    download(f"https://alphafold.ebi.ac.uk/api/prediction/{UNIPROT_ID}", alphafold_api)
    af_records = load_json(alphafold_api)
    if not isinstance(af_records, list) or not af_records:
        raise RuntimeError("AlphaFold API returned no prediction record")
    af_record = af_records[0]
    alphafold_pdb = STRUCTURE_DIR / f"{af_record['entryId']}.pdb"
    download(af_record["pdbUrl"], alphafold_pdb)

    rows: list[dict[str, str | float]] = []
    for selection in PDB_SELECTIONS:
        pdb_id = selection["pdb_id"]
        entry_json = METADATA_DIR / f"rcsb_{pdb_id}_entry.json"
        entity_json = METADATA_DIR / f"rcsb_{pdb_id}_entity_1.json"
        pdb_file = STRUCTURE_DIR / f"{pdb_id}.pdb"
        cif_file = STRUCTURE_DIR / f"{pdb_id}.cif"

        download(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}", entry_json)
        download(f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/1", entity_json)
        download(f"https://files.rcsb.org/download/{pdb_id}.pdb", pdb_file)
        download(f"https://files.rcsb.org/download/{pdb_id}.cif", cif_file)

        entry = load_json(entry_json)
        entity = load_json(entity_json)
        rows.append(
            {
                "target_id": "EGFR",
                "uniprot_id": UNIPROT_ID,
                "variant": selection["variant"],
                "pdb_id": pdb_id,
                "expected_mutations": selection["expected_mutations"],
                "depositor_mutation_flag": entity.get("rcsb_polymer_entity", {}).get(
                    "pdbx_mutation", ""
                )
                or "",
                "auth_chains": ";".join(
                    entity.get("rcsb_polymer_entity_container_identifiers", {}).get(
                        "auth_asym_ids", []
                    )
                ),
                "method": entry.get("exptl", [{}])[0].get("method", ""),
                "resolution_angstrom": (
                    entry.get("rcsb_entry_info", {}).get("resolution_combined", [""])[0]
                ),
                "title": entry.get("struct", {}).get("title", ""),
                "role": selection["role"],
                "source_url": f"https://www.rcsb.org/structure/{pdb_id}",
                "retrieved_at": retrieved_at,
                "pdb_sha256": sha256(pdb_file),
                "cif_sha256": sha256(cif_file),
            }
        )

    manifest_path = TARGET_DIR / "egfr_structure_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    provenance = {
        "retrieved_at": retrieved_at,
        "uniprot": {
            "accession": UNIPROT_ID,
            "fasta_url": f"https://rest.uniprot.org/uniprotkb/{UNIPROT_ID}.fasta",
            "metadata_url": f"https://rest.uniprot.org/uniprotkb/{UNIPROT_ID}.json",
            "fasta_sha256": sha256(uniprot_fasta),
        },
        "alphafold": {
            "entry_id": af_record["entryId"],
            "model_created_date": af_record.get("modelCreatedDate"),
            "pdb_url": af_record["pdbUrl"],
            "pdb_sha256": sha256(alphafold_pdb),
        },
        "experimental_structures": [item["pdb_id"] for item in PDB_SELECTIONS],
    }
    (TARGET_DIR / "provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "target_dir": str(TARGET_DIR),
                "uniprot": UNIPROT_ID,
                "alphafold_entry": af_record["entryId"],
                "pdb_entries": [item["pdb_id"] for item in PDB_SELECTIONS],
                "manifest": str(manifest_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
