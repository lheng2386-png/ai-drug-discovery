# EGFR known ligands

Build the curated table with:

```bash
conda run -n drug-align-analysis python scripts/build_egfr_known_ligands.py
```

## Selection rules

- ChEMBL target: `CHEMBL203` (human EGFR)
- binding assays only
- exact (`=`) standardized measurements
- nM units
- pChEMBL >= 6
- activity types: IC50, Ki, Kd
- records with ChEMBL validity warnings or duplicate flags are excluded

## Output semantics

`egfr_known_ligands.csv` contains one row per:

```text
standardized InChIKey × normalized assay mutation set × activity type
```

Multiple measurements are summarized by the best and median nM value, with all
assay and document identifiers retained. Multiple ChEMBL molecule IDs that
collapse to the same standardized chemical identity are preserved in
`all_molecule_chembl_ids`.

An `unspecified` mutation label means that ChEMBL did not supply a variant for
the assay. It must not be interpreted as confirmed wild type.

## Current snapshot

- downloaded activities: 13,689
- retained IC50/Ki/Kd activities: 13,439
- aggregated rows: 10,437
- standardized chemical identities: 8,298
- invalid SMILES: 0

The full raw API response is stored locally as compressed JSON Lines and is
excluded from Git.
