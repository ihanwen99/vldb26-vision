# VLDB26-Vision

PEAQ: A DBMS-Inspired Planning, Executing, and Adapting Framework for Scalable Quantum Annealing

---

This repository contains the source code and evaluation results used in this paper:
- Build QUBOs from query instances, decompose into two subproblems.
- Reuse variable-to-qubit mappings.
- Compare fusion strategies (M0/M1/M2) for sampling results.

## Repository layout
- `Problems/`: input instances (per-relation folders, 50 instances each).
- `pipelines/`:
  - `reuse_mapping_pipeline.py`: Reuse vs non-reuse with variable-to-qubit mappings.
  - `fusion_pipeline.py`: Compare M0/M1/M2 fusion strategies.
- `cpp/`: C++ implementation and Python wrapper for the seeded greedy mapping approach.
- `benchmark.sh`: Benchmark script.
- `results/`: Output files for generating tables and figures in the paper.

## Requirements
- Python 3.9+
- D-Wave credentials configured for `DWaveSampler`
- C++ compiler (`g++` or `clang++`)

Build the C++ mapping library (for accelerating the computation):
```bash
g++ -O3 -std=c++17 -shared -fPIC -o cpp/cpp_embed_greedy_lib.so cpp/cpp_embed_greedy.cpp
```

## Data format
Each instance directory contains:
```
Problems/<graph_type>/<relations>/<instance_id>/
  cardinalities.json
  selectivities.json
```

## Quick start
Run reuse vs non-reuse (saves BQMs/mappings and reports quality):
```bash
python3 pipelines/reuse_mapping_pipeline.py \
  --root Problems \
  --relations 10relations \
  --limit 10 \
  --out-dir results/reuse_mapping
```

Run fusion strategies on the latest run directory:
```bash
python3 pipelines/fusion_pipeline.py \
  --latest \
  --runs-root results/reuse_mapping \
  --problems-root Problems \
  --k 1 2 3 \
  --num-reads 100
```

Batch experiments:
```bash
bash benchmark.sh
```

## Outputs
Each run creates a subfolder under `results/reuse_mapping/`:
- `results.csv`: per-instance metrics (reuse vs non-reuse).
- `bqms/`: saved `full_original` and `v/rest` target BQMs + mappings.
- `fusion/`: fusion metrics (M0/M1/M2) when running `fusion_pipeline.py`.

## Notes
- Default paths in code are absolute; use CLI flags (`--root`, `--out-dir`,
  `--runs-root`, `--problems-root`) to point to your local setup.
