#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$PWD}"
NUM_SAMPLES="${2:-250}"
BATCH_SIZE="${3:-8}"
DEVICE="${4:-cuda:0}"

TARGETDIFF_DIR="${PROJECT_ROOT}/external/targetdiff"
CHECKPOINT="${TARGETDIFF_DIR}/pretrained_models/pretrained_diffusion.pt"
CONFIG="${PROJECT_ROOT}/configs/targetdiff/egfr_smoke.yml"
POCKET_DIR="${PROJECT_ROOT}/data/pockets/egfr"
RUN_ID="targetdiff_egfr_$(date -u +%Y%m%dT%H%M%SZ)"
RESULT_ROOT="${PROJECT_ROOT}/results/generation/raw/${RUN_ID}"

test -d "${TARGETDIFF_DIR}" || {
  echo "Missing TargetDiff source: ${TARGETDIFF_DIR}" >&2
  echo "Run scripts/cloud/setup_targetdiff.sh first." >&2
  exit 2
}
test -f "${CHECKPOINT}" || {
  echo "Missing TargetDiff checkpoint: ${CHECKPOINT}" >&2
  echo "Download the official pretrained_diffusion.pt into external/targetdiff/pretrained_models/." >&2
  exit 2
}
test -f "${CONFIG}" || {
  echo "Missing config: ${CONFIG}" >&2
  exit 2
}
test -d "${POCKET_DIR}" || {
  echo "Missing EGFR pocket directory: ${POCKET_DIR}" >&2
  exit 2
}

mapfile -t POCKETS < <(find "${POCKET_DIR}" -maxdepth 1 -type f -name "*_pocket_10A.pdb" | sort)
if [[ "${#POCKETS[@]}" -eq 0 ]]; then
  echo "No 10A EGFR pocket PDB files found in ${POCKET_DIR}" >&2
  exit 2
fi

mkdir -p "${RESULT_ROOT}"
nvidia-smi

echo "TargetDiff EGFR generation"
echo "project_root=${PROJECT_ROOT}"
echo "num_samples_per_pocket=${NUM_SAMPLES}"
echo "batch_size=${BATCH_SIZE}"
echo "device=${DEVICE}"
echo "result_root=${RESULT_ROOT}"

cd "${TARGETDIFF_DIR}"
for POCKET in "${POCKETS[@]}"; do
  POCKET_BASENAME="$(basename "${POCKET}" .pdb)"
  OUTDIR="${RESULT_ROOT}/${POCKET_BASENAME}"
  mkdir -p "${OUTDIR}"
  echo "Running TargetDiff on ${POCKET_BASENAME}"
  conda run -n targetdiff python scripts/sample_for_pocket.py \
    "${CONFIG}" \
    --pdb_path "${POCKET}" \
    --device "${DEVICE}" \
    --num_samples "${NUM_SAMPLES}" \
    --batch_size "${BATCH_SIZE}" \
    --result_path "${OUTDIR}"
done

echo "TargetDiff raw outputs are in ${RESULT_ROOT}"
echo "Next postprocess example:"
echo "conda run -n drug-evaluation python scripts/postprocess_generated_ligands.py \\"
echo "  --sdf-dir ${RESULT_ROOT} \\"
echo "  --out-prefix results/generation/egfr_first_batch/generated_egfr_candidates"
