# TargetDiff baseline configuration

## Pinned source

- Repository: `https://github.com/guanjq/targetdiff`
- Commit: `142f1eb7178480d435fe0b8cb95a99beb48997c7`
- Official tested stack: Python 3.8, PyTorch 1.13.1, CUDA 11.6,
  PyTorch Geometric 2.2.0, RDKit 2022.03.2

The local clone lives at `external/targetdiff/` and is excluded from Git. The
commit hash is recorded here so a cloud instance can reproduce the same source.

## Input policy

TargetDiff's official `sample_for_pocket.py` expects a protein-only PDB pocket
clipped to 10 Å around a reference ligand. Therefore:

- 6 Å EGFR pockets are retained for local representation/alignment;
- 10 Å EGFR pockets are used for TargetDiff generation;
- ligand HETATM records, waters, ions, and unrelated hetero residues are not
  included in the protein pocket file;
- the reference ligand is used only to define the pocket and is stored
  separately.

First smoke input:

```text
data/pockets/egfr/4G5J_WT_pocket_10A.pdb
```

Because `4G5J` contains covalent afatinib, it is suitable for pipeline
validation but must not be treated as a neutral non-covalent benchmark.

## Cloud command outline

```bash
git clone https://github.com/guanjq/targetdiff.git
cd targetdiff
git checkout 142f1eb7178480d435fe0b8cb95a99beb48997c7
conda env create -f /path/to/targetdiff-cloud.yml
conda activate targetdiff
python scripts/sample_for_pocket.py configs/sampling.yml \
  --pdb_path /path/to/4G5J_WT_pocket_10A.pdb \
  --num_samples 10 \
  --batch_size 2 \
  --result_path outputs/egfr_4g5j_smoke
```

The pretrained checkpoint path in `configs/sampling.yml` must be set after the
official checkpoint is downloaded. A successful environment import is not
equivalent to a successful generation run.

Repository scripts:

- `scripts/validate_targetdiff_inputs.py`: checks all 10 Å EGFR pockets with
  the pinned TargetDiff `PDBProtein` parser;
- `scripts/cloud/setup_targetdiff.sh`: restores the pinned source and Conda
  environment on Ubuntu;
- `scripts/cloud/run_targetdiff_egfr_smoke.sh`: runs 10 samples from the WT
  EGFR pocket after the official checkpoint is present.

Local static validation passed for four pockets. This does not establish that
the CUDA environment, checkpoint, reconstruction, or sampling pipeline works.

## Hardware decision

Use Ubuntu x86_64 and an NVIDIA Ampere GPU for the first reproduction. RTX 3090
24 GB is preferred over RTX 5090 because the official CUDA 11.6/PyTorch 1.13
stack predates Blackwell support. A modernized stack for RTX 5090 is a separate
compatibility experiment, not the reference baseline.
