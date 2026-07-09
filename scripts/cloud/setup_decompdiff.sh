#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$PWD}"
DECOMPDIFF_DIR="${PROJECT_ROOT}/external/decompdiff"
DECOMPDIFF_COMMIT="ed4e7d8202c077cc4bd1b9ca626e173c24007f2a"

if [[ ! -d "${DECOMPDIFF_DIR}/.git" ]]; then
  git clone https://github.com/bytedance/DecompDiff.git "${DECOMPDIFF_DIR}"
fi

git -C "${DECOMPDIFF_DIR}" fetch --all --tags
git -C "${DECOMPDIFF_DIR}" checkout "${DECOMPDIFF_COMMIT}"

conda env create \
  -f "${PROJECT_ROOT}/environment/decompdiff-cloud.yml" \
  --yes

echo "DecompDiff source and Conda environment are prepared."
echo "Sampling is not ready until checkpoint, processed dataset/index,"
echo "and EGFR AlphaSpace/reference-ligand decomposition are available."
