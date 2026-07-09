# Portable research snapshot

`egfr_research_snapshot_2026-07-09.tar.gz` is a migration archive created
because the GitHub upload helper intentionally filters raw data and generated
outputs.

It contains:

- EGFR UniProt sequence, RCSB structures, AlphaFold structure, and API metadata
- 6 Å and 10 Å EGFR pockets plus reference-ligand PDB files
- compressed raw ChEMBL activity response
- lightweight processed PLINDER sample tables
- ESM-2, SaProt, and Uni-Mol smoke-test embeddings

It does not contain:

- the approximately 463 MB PLINDER raw snapshot
- model weights or Hugging Face caches
- the local TargetDiff clone
- logs, credentials, or environment secrets

SHA-256:

```text
285eb3c046c173bb72e859094c336707a44d4f2f87f211b284d72bdd272aae39
```

Restore from the repository root:

```bash
tar -xzf portable_snapshot/egfr_research_snapshot_2026-07-09.tar.gz
```
