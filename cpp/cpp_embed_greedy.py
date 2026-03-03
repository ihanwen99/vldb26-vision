import ctypes
import os
from typing import Dict, Hashable, Optional, Tuple

import dimod
import numpy as np

LIB_NAME = "cpp_embed_greedy_lib.so"
LIB_PATH = os.path.join(os.path.dirname(__file__), LIB_NAME)


class CppEmbedGreedyError(RuntimeError):
    pass


def _load_lib() -> ctypes.CDLL:
    if not os.path.exists(LIB_PATH):
        raise CppEmbedGreedyError(
            f"C++ library not found at {LIB_PATH}. Build it first with: "
            f"g++ -O3 -std=c++17 -shared -fPIC -o {LIB_PATH} "
            f"{os.path.join(os.path.dirname(__file__), 'cpp_embed_greedy.cpp')}"
        )
    lib = ctypes.CDLL(LIB_PATH)

    lib.embed_seeded_neighbor_greedy_cpp.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.embed_seeded_neighbor_greedy_cpp.restype = ctypes.c_int

    lib.embed_last_error.argtypes = []
    lib.embed_last_error.restype = ctypes.c_char_p

    return lib


def embed_seeded_neighbor_greedy_cpp(
    bqm: dimod.BinaryQuadraticModel,
    sampler,
    *,
    rng_seed: int = 0,
) -> Tuple[dimod.BinaryQuadraticModel, Dict[Hashable, int], Dict[str, str]]:
    nodelist = list(sampler.nodelist)
    edgelist = list(sampler.edgelist)

    variables = list(bqm.variables)
    n_vars = len(variables)
    var_to_idx = {v: i for i, v in enumerate(variables)}

    quad_u = []
    quad_v = []
    quad_w = []
    for (u, v), w in bqm.quadratic.items():
        quad_u.append(var_to_idx[u])
        quad_v.append(var_to_idx[v])
        quad_w.append(float(w))

    linear_bias = [float(bqm.linear[v]) for v in variables]

    quad_u_arr = np.asarray(quad_u, dtype=np.int32)
    quad_v_arr = np.asarray(quad_v, dtype=np.int32)
    quad_w_arr = np.asarray(quad_w, dtype=np.float64)
    linear_arr = np.asarray(linear_bias, dtype=np.float64)

    node_arr = np.asarray(nodelist, dtype=np.int32)
    edge_u_arr = np.asarray([a for a, _ in edgelist], dtype=np.int32)
    edge_v_arr = np.asarray([b for _, b in edgelist], dtype=np.int32)

    out_mapping = np.empty(n_vars, dtype=np.int32)
    mapping_ms = ctypes.c_double(0.0)

    lib = _load_lib()
    rc = lib.embed_seeded_neighbor_greedy_cpp(
        ctypes.c_int(n_vars),
        quad_u_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        quad_v_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        quad_w_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_int(len(quad_u_arr)),
        linear_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        node_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        ctypes.c_int(len(node_arr)),
        edge_u_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        edge_v_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        ctypes.c_int(len(edge_u_arr)),
        ctypes.c_uint(rng_seed),
        out_mapping.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        ctypes.byref(mapping_ms),
    )

    if rc != 0:
        err = lib.embed_last_error().decode("utf-8", errors="ignore")
        raise CppEmbedGreedyError(f"C++ greedy embed failed (code {rc}): {err}")

    mapping = {variables[i]: int(out_mapping[i]) for i in range(n_vars)}

    stats = {
        "find_mapping_time_ms": f"{mapping_ms.value:.2f}",
    }

    return None, mapping, stats
