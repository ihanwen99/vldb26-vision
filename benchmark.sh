#!/usr/bin/env bash
set -euo pipefail

ROOT="/tank/users/hanwen/vldb26-vision"
PROBLEMS="$ROOT/Problems"
RESULTS="$ROOT/results/reuse_mapping"

source /tank/users/hanwen/miniconda3/etc/profile.d/conda.sh
conda activate quantum

for REL in 20 30 40 50 60 70; do
  python3 "$ROOT/pipelines/reuse_mapping_pipeline.py" --relations "${REL}relations" --limit 50 --out-dir "$RESULTS"
  python3 "$ROOT/pipelines/fusion_pipeline.py" \
    --latest \
    --runs-root "$RESULTS" \
    --problems-root "$PROBLEMS" \
    --k 1 2 3 \
    --num-reads 100
done
