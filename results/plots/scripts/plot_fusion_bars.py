#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Embedded fusion means data (avg energy, avg db_cost).
fusion_results = {
  "70relations": {
    "M0": [
      19467587.55112635,
      4.597900311930036e+155
    ],
    "M2": [
      9175062.800330862,
      4.597900311930036e+155
    ],
    "M1-2": [
      19396567.4060003,
      4.597896539743634e+155
    ],
    "M1-3": [
      19372437.215494312,
      2.815900820338331e+146
    ],
    "M1-4": [
      19337165.8209743,
      2.17541412713726e+152
    ],
    "M1-5": [
      19318183.703536287,
      2.175411359795239e+152
    ]
  },
  "40relations": {
    "M0": [
      2147746.979201999,
      5.704477937335019e+100
    ],
    "M2": [
      677289.5307420166,
      5.704477937335019e+100
    ],
    "M1-2": [
      2132109.169058002,
      1.3005578425560867e+98
    ],
    "M1-3": [
      2125689.0495960037,
      1.3005583993727124e+98
    ],
    "M1-4": [
      2119892.8104540035,
      1.3011349507284332e+98
    ],
    "M1-5": [
      2115643.107714004,
      1.2987324913304463e+98
    ]
  },
  "20relations": {
    "M0": [
      108315.92744400012,
      1.7107484695118269e+50
    ],
    "M2": [
      41819.86927200007,
      1.7107484695118269e+50
    ],
    "M1-2": [
      106772.72232200015,
      5.553048748715702e+55
    ],
    "M1-3": [
      106096.90820600011,
      1.3861936072376922e+63
    ],
    "M1-4": [
      105481.52130600011,
      1.3861936072376922e+63
    ],
    "M1-5": [
      105135.9180220001,
      1.3861936072376922e+63
    ]
  },
  "60relations": {
    "M0": [
      10685729.013325965,
      8.545199843480046e+135
    ],
    "M2": [
      4549131.074578232,
      8.545199843480046e+135
    ],
    "M1-2": [
      10638337.121707972,
      3.718933464569273e+127
    ],
    "M1-3": [
      10604715.985249965,
      6.348448978968574e+133
    ],
    "M1-4": [
      10597877.19959997,
      2.8025113021432217e+127
    ],
    "M1-5": [
      10587834.164185964,
      2.8025113021543694e+127
    ]
  },
  "50relations": {
    "M0": [
      5243391.519628072,
      1.1434372216478286e+116
    ],
    "M2": [
      1950921.9208300016,
      1.1434372216478286e+116
    ],
    "M1-2": [
      5219617.8268300705,
      3.794345423442869e+106
    ],
    "M1-3": [
      5199165.227364073,
      6.90384545269524e+102
    ],
    "M1-4": [
      5195618.782766076,
      1.0667987391121956e+109
    ],
    "M1-5": [
      5190890.902454075,
      3.072564962526612e+112
    ]
  },
  "30relations": {
    "M0": [
      651332.0730039985,
      4.4132938149500184e+73
    ],
    "M2": [
      183013.46287199936,
      4.4132938149500184e+73
    ],
    "M1-2": [
      644653.145165999,
      1.7099262407382614e+73
    ],
    "M1-3": [
      641652.8897599991,
      8.886301784402858e+73
    ],
    "M1-4": [
      640073.4896159988,
      4.092135244952927e+75
    ],
    "M1-5": [
      638452.0097999988,
      4.092083355629844e+75
    ]
  }
}


import argparse
import math
import os

import matplotlib.pyplot as plt


def safe_log10(x: float) -> float:
    return math.log10(max(x, 1e-12))


def compute_means_from_embedded():
    means = {}
    for rel, variants in fusion_results.items():
        means[rel] = {}
        for var, pair in variants.items():
            means[rel][var] = (float(pair[0]), float(pair[1]))
    return means


def plot_bars(means, out_path_energy, out_path_cost):
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]
    relations = sorted(means.keys(), key=lambda s: int("".join(ch for ch in s if ch.isdigit()) or 0))
    variants = ["M0", "M1-2", "M1-3", "M2"]

    x = range(len(relations))
    width = 0.18

    plt.figure(figsize=(12, 5))
    # ColorBrewer Set2 (muted, professional)
    colors = ["#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3", "#A6D854", "#FFD92F"]
    for i, var in enumerate(variants):
        vals = []
        for r in relations:
            e = means.get(r, {}).get(var, (None, None))[0]
            vals.append(safe_log10(e) if e is not None else 0.0)
        plt.bar([xi + (i - 1.5) * width for xi in x], vals, width=width, label=var, color=colors[i])
    plt.xticks(list(x), relations, rotation=0)
    plt.ylabel("log10(Energy)")
    plt.legend(ncol=len(variants), loc="upper center", bbox_to_anchor=(0.5, 0.98), frameon=True)
    plt.tight_layout()
    plt.savefig(out_path_energy, dpi=200)
    plt.savefig(out_path_energy.replace(".png", ".pdf"))
    plt.close()

    plt.figure(figsize=(12, 5))
    for i, var in enumerate(variants):
        vals = []
        for r in relations:
            c = means.get(r, {}).get(var, (None, None))[1]
            vals.append(safe_log10(c) if c is not None else 0.0)
        plt.bar([xi + (i - 1.5) * width for xi in x], vals, width=width, label=var, color=colors[i])
    plt.xticks(list(x), relations, rotation=0)
    plt.ylabel("log10(DB Cost)")
    plt.legend(ncol=len(variants), loc="upper center", bbox_to_anchor=(0.5, 0.98), frameon=True)
    plt.tight_layout()
    plt.savefig(out_path_cost, dpi=200)
    plt.savefig(out_path_cost.replace(".png", ".pdf"))
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Plot fusion strategy bars by relation size.")
    parser.add_argument("--out-dir", default="/tank/users/hanwen/vldb26-vision/results/plots",
                        help="Output directory for plots")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    means = compute_means_from_embedded()
    out_energy = os.path.join(args.out_dir, "fusion_log_energy.png")
    out_cost = os.path.join(args.out_dir, "fusion_log_db_cost.png")
    plot_bars(means, out_energy, out_cost)
    print(f"[DONE] {out_energy}")
    print(f"[DONE] {out_cost}")


if __name__ == "__main__":
    main()
