# New-computer setup

## Restore the repository

```bash
git clone https://github.com/lheng2386-png/ai-drug-discovery.git
cd ai-drug-discovery
conda env create -f environment/analysis-environment.yml
conda activate drug-align-analysis
```

## Verify the portable snapshot

```bash
python scripts/download_egfr_data.py
python scripts/extract_egfr_pockets.py
python -m py_compile scripts/*.py
```

The repository contains the compact EGFR sequence/structure snapshot, 10 Å
TargetDiff pocket inputs, the curated ChEMBL ligand table, and small ESM-2,
SaProt, and Uni-Mol smoke-test embeddings. The commands above can independently
rebuild the downloaded data and pockets.

## Data intentionally not stored in GitHub

- PLINDER raw snapshot (approximately 463 MB)
- pretrained model weights and Hugging Face caches
- the local clone of the TargetDiff repository
- runtime logs and Python caches

These items are reproducible and would unnecessarily inflate Git history.

## Restore TargetDiff source

```bash
git clone https://github.com/guanjq/targetdiff.git external/targetdiff
git -C external/targetdiff checkout 142f1eb7178480d435fe0b8cb95a99beb48997c7
```

TargetDiff generation still requires an Ubuntu x86_64 NVIDIA machine and the
official pretrained checkpoint. See `docs/targetdiff-baseline.md`.
