#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$PWD}"
TARGETDIFF_DIR="${PROJECT_ROOT}/external/targetdiff"
CHECKPOINT="${TARGETDIFF_DIR}/pretrained_models/pretrained_diffusion.pt"
POCKET="${PROJECT_ROOT}/data/pockets/egfr/4G5J_WT_pocket_10A.pdb"
CONFIG="${PROJECT_ROOT}/configs/targetdiff/egfr_smoke.yml"
RESULTS="${PROJECT_ROOT}/results/targetdiff/egfr_4g5j_smoke"

test -f "${CHECKPOINT}" || {
  echo "Missing checkpoint: ${CHECKPOINT}" >&2
  exit 2
}
test -f "${POCKET}" || {
  echo "Missing pocket: ${POCKET}" >&2
  exit 2
}
nvidia-smi

cd "${TARGETDIFF_DIR}"
conda run -n targetdiff python scripts/sample_for_pocket.py \
  "${CONFIG}" \
  --pdb_path "${POCKET}" \
  --device cuda:0 \
  --num_samples 10 \
  --batch_size 2 \
  --result_path "${RESULTS}"
