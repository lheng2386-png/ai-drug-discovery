#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$PWD}"
TARGETDIFF_DIR="${PROJECT_ROOT}/external/targetdiff"
TARGETDIFF_COMMIT="142f1eb7178480d435fe0b8cb95a99beb48997c7"

if [[ ! -d "${TARGETDIFF_DIR}/.git" ]]; then
  git clone https://github.com/guanjq/targetdiff.git "${TARGETDIFF_DIR}"
fi

git -C "${TARGETDIFF_DIR}" fetch --all --tags
git -C "${TARGETDIFF_DIR}" checkout "${TARGETDIFF_COMMIT}"

conda env create \
  -f "${PROJECT_ROOT}/environment/targetdiff-cloud.yml" \
  --yes

echo "TargetDiff source and Conda environment are prepared."
echo "Next: download the official pretrained_diffusion.pt checkpoint."
echo "Then run scripts/cloud/run_targetdiff_egfr_smoke.sh."
