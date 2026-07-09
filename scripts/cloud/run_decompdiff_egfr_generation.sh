#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$PWD}"
DATA_ID="${2:-0}"
BATCH_SIZE="${3:-8}"
DEVICE="${4:-cuda:0}"

DECOMPDIFF_DIR="${PROJECT_ROOT}/external/decompdiff"
CONFIG="${DECOMPDIFF_DIR}/configs/sampling_drift.yml"

: "${DECOMPDIFF_CKPT:?Set DECOMPDIFF_CKPT to the DecompDiff checkpoint path.}"
: "${DECOMPDIFF_ORI_DATA:?Set DECOMPDIFF_ORI_DATA to the processed original data path.}"
: "${DECOMPDIFF_INDEX:?Set DECOMPDIFF_INDEX to the processed test index .pkl path.}"

PRIOR_MODE="${DECOMPDIFF_PRIOR_MODE:-ref_prior}"
NUM_ATOMS_MODE="${DECOMPDIFF_NUM_ATOMS_MODE:-ref}"
RUN_ID="decompdiff_egfr_$(date -u +%Y%m%dT%H%M%SZ)"
OUTDIR="${PROJECT_ROOT}/results/generation/raw/${RUN_ID}"

test -d "${DECOMPDIFF_DIR}" || {
  echo "Missing DecompDiff source: ${DECOMPDIFF_DIR}" >&2
  echo "Run scripts/cloud/setup_decompdiff.sh first." >&2
  exit 2
}
test -f "${DECOMPDIFF_CKPT}" || {
  echo "Missing DecompDiff checkpoint: ${DECOMPDIFF_CKPT}" >&2
  exit 2
}
test -d "${DECOMPDIFF_ORI_DATA}" || {
  echo "Missing DecompDiff processed data directory: ${DECOMPDIFF_ORI_DATA}" >&2
  exit 2
}
test -f "${DECOMPDIFF_INDEX}" || {
  echo "Missing DecompDiff index file: ${DECOMPDIFF_INDEX}" >&2
  exit 2
}

mkdir -p "${OUTDIR}"
nvidia-smi

echo "DecompDiff EGFR generation via official indexed-dataset sampler"
echo "project_root=${PROJECT_ROOT}"
echo "data_id=${DATA_ID}"
echo "batch_size=${BATCH_SIZE}"
echo "device=${DEVICE}"
echo "prior_mode=${PRIOR_MODE}"
echo "num_atoms_mode=${NUM_ATOMS_MODE}"
echo "outdir=${OUTDIR}"

cd "${DECOMPDIFF_DIR}"
conda run -n decompdiff python scripts/sample_diffusion_decomp.py \
  "${CONFIG}" \
  --ori_data_path "${DECOMPDIFF_ORI_DATA}" \
  --index_path "${DECOMPDIFF_INDEX}" \
  --ckpt_path "${DECOMPDIFF_CKPT}" \
  --outdir "${OUTDIR}" \
  --data_id "${DATA_ID}" \
  --device "${DEVICE}" \
  --batch_size "${BATCH_SIZE}" \
  --prior_mode "${PRIOR_MODE}" \
  --num_atoms_mode "${NUM_ATOMS_MODE}"

echo "DecompDiff raw output is in ${OUTDIR}"
echo "If result.pt was produced, postprocess with:"
echo "conda run -n drug-evaluation python scripts/postprocess_generated_ligands.py \\"
echo "  --decompdiff-pt ${OUTDIR}/sampling_drift_*/result.pt \\"
echo "  --out-prefix results/generation/egfr_first_batch/generated_egfr_candidates"
