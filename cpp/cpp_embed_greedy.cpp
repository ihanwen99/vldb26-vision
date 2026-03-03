#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <random>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

thread_local std::string g_last_error;

static int64_t edge_key(int a, int b) {
    if (a > b) std::swap(a, b);
    return (static_cast<int64_t>(a) << 32) | static_cast<uint32_t>(b);
}

static bool has_neighbor(const std::vector<std::vector<int>> &adj, int qpos, int neighbor_pos) {
    const auto &neighbors = adj[qpos];
    return std::binary_search(neighbors.begin(), neighbors.end(), neighbor_pos);
}

static void build_weight_adj(
    int n_vars,
    const int *quad_u,
    const int *quad_v,
    const double *quad_w,
    int m,
    std::vector<std::unordered_map<int, double>> &weight_adj,
    std::vector<double> &abs_weight_sum
) {
    weight_adj.assign(n_vars, {});
    abs_weight_sum.assign(n_vars, 0.0);
    for (int i = 0; i < m; ++i) {
        int u = quad_u[i];
        int v = quad_v[i];
        if (u < 0 || v < 0 || u >= n_vars || v >= n_vars || u == v) {
            continue;
        }
        double w = quad_w[i];
        if (w < 0) w = -w;
        weight_adj[u][v] = w;
        weight_adj[v][u] = w;
        abs_weight_sum[u] += w;
        abs_weight_sum[v] += w;
    }
}

static bool build_mapping_seeded_neighbor_greedy(
    int n_vars,
    const std::vector<std::vector<int>> &phys_adj,
    const std::vector<int> &phys_deg,
    const std::vector<int> &qubits_ids,
    const std::vector<std::unordered_map<int, double>> &weight_adj,
    const std::vector<double> &abs_weight_sum,
    std::vector<int> &mapping_pos
) {
    if (static_cast<int>(phys_adj.size()) < n_vars) return false;

    int seed_var = 0;
    double best_sum = -1.0;
    for (int v = 0; v < n_vars; ++v) {
        if (abs_weight_sum[v] > best_sum) {
            best_sum = abs_weight_sum[v];
            seed_var = v;
        }
    }

    int starting_qpos = 0;
    int best_deg = -1;
    for (size_t i = 0; i < phys_deg.size(); ++i) {
        if (phys_deg[i] > best_deg) {
            best_deg = phys_deg[i];
            starting_qpos = static_cast<int>(i);
        }
    }

    mapping_pos.assign(n_vars, -1);
    std::vector<char> assigned(n_vars, 0);
    std::vector<int> variables_assigned;
    variables_assigned.reserve(n_vars);

    std::vector<char> used_qubits(phys_adj.size(), 0);
    std::vector<int> qubits_assigned;
    qubits_assigned.reserve(n_vars);

    mapping_pos[seed_var] = starting_qpos;
    assigned[seed_var] = 1;
    variables_assigned.push_back(seed_var);
    used_qubits[starting_qpos] = 1;
    qubits_assigned.push_back(starting_qpos);

    // Incremental scores: maintain per-qpos scores to avoid O(N^3) full scans.
    std::vector<std::unordered_map<int, double>> score_maps(phys_adj.size());
    auto update_scores_for_new_var = [&](int new_var, int new_qpos) {
        for (const auto &kv : weight_adj[new_var]) {
            int v = kv.first;
            if (assigned[v]) continue;
            double w = kv.second;
            for (int qpos_n : phys_adj[new_qpos]) {
                score_maps[qpos_n][v] += w;
            }
        }
    };
    update_scores_for_new_var(seed_var, starting_qpos);

    auto pick_smallest_unassigned = [&]() -> int {
        for (int v = 0; v < n_vars; ++v) {
            if (!assigned[v]) return v;
        }
        return -1;
    };

    auto neighbor_pool = [&]() {
        std::vector<int> pool;
        std::vector<char> in_pool(phys_adj.size(), 0);
        for (int qpos : qubits_assigned) {
            for (int nb : phys_adj[qpos]) {
                if (!used_qubits[nb] && !in_pool[nb]) {
                    in_pool[nb] = 1;
                    pool.push_back(nb);
                }
            }
        }
        std::sort(pool.begin(), pool.end());
        return pool;
    };

    auto distance_to_last = [&](int qpos) -> int {
        int last_pos = qubits_assigned.back();
        int last_id = qubits_ids[last_pos];
        int q_id = qubits_ids[qpos];
        int d = q_id - last_id;
        return d < 0 ? -d : d;
    };

    auto candidates = neighbor_pool();
    int remaining = n_vars - 1;
    while (remaining > 0) {
        if (candidates.empty()) {
            for (size_t i = 0; i < phys_adj.size(); ++i) {
                if (!used_qubits[i]) candidates.push_back(static_cast<int>(i));
            }
            std::sort(candidates.begin(), candidates.end());
            if (candidates.empty()) return false;
        }

        int best_col = -1;
        double best_col_score = -1e300;
        int best_col_var = -1;

        for (int qpos : candidates) {
            double col_best_score = -1e300;
            int col_best_var = -1;

            auto &scores = score_maps[qpos];
            for (const auto &kv : scores) {
                int v = kv.first;
                if (assigned[v]) continue;
                double s = kv.second;
                if (s > col_best_score) {
                    col_best_score = s;
                    col_best_var = v;
                }
            }
            if (col_best_var < 0) {
                col_best_var = pick_smallest_unassigned();
                col_best_score = 0.0;
            }

            if (col_best_score > best_col_score) {
                best_col_score = col_best_score;
                best_col = qpos;
                best_col_var = col_best_var;
            } else if (col_best_score == best_col_score && best_col != -1) {
                if (distance_to_last(qpos) < distance_to_last(best_col)) {
                    best_col = qpos;
                    best_col_var = col_best_var;
                }
            }
        }

        int new_qpos = best_col;
        int new_v = best_col_var;
        if (new_qpos < 0 || new_v < 0) return false;

        mapping_pos[new_v] = new_qpos;
        assigned[new_v] = 1;
        variables_assigned.push_back(new_v);
        used_qubits[new_qpos] = 1;
        qubits_assigned.push_back(new_qpos);
        remaining -= 1;

        update_scores_for_new_var(new_v, new_qpos);
        candidates = neighbor_pool();
    }

    return true;
}

}  // namespace

extern "C" {

int embed_seeded_neighbor_greedy_cpp(
    int n_vars,
    const int *quad_u,
    const int *quad_v,
    const double *quad_w,
    int quad_m,
    const double *linear_bias,
    const int *node_list,
    int node_count,
    const int *edge_u,
    const int *edge_v,
    int edge_count,
    unsigned int rng_seed,
    int *out_mapping,
    double *out_mapping_ms
) {
    try {
        if (n_vars <= 0 || node_count <= 0) {
            g_last_error = "Invalid n_vars or node_count";
            return 1;
        }

        auto t0 = std::chrono::high_resolution_clock::now();

        std::vector<int> qubits_ids(node_list, node_list + node_count);
        std::unordered_map<int, int> id_to_pos;
        id_to_pos.reserve(node_count * 2);
        for (int i = 0; i < node_count; ++i) {
            id_to_pos[qubits_ids[i]] = i;
        }

        std::vector<std::vector<int>> phys_adj(node_count);
        std::vector<int> phys_deg(node_count, 0);
        for (int i = 0; i < edge_count; ++i) {
            int u_id = edge_u[i];
            int v_id = edge_v[i];
            auto it_u = id_to_pos.find(u_id);
            auto it_v = id_to_pos.find(v_id);
            if (it_u == id_to_pos.end() || it_v == id_to_pos.end()) continue;
            int u = it_u->second;
            int v = it_v->second;
            if (u == v) continue;
            phys_adj[u].push_back(v);
            phys_adj[v].push_back(u);
            phys_deg[u] += 1;
            phys_deg[v] += 1;
        }
        for (auto &nbrs : phys_adj) {
            std::sort(nbrs.begin(), nbrs.end());
        }

        std::vector<std::unordered_map<int, double>> weight_adj;
        std::vector<double> abs_weight_sum;
        build_weight_adj(n_vars, quad_u, quad_v, quad_w, quad_m, weight_adj, abs_weight_sum);

        std::vector<int> mapping_pos;
        if (!build_mapping_seeded_neighbor_greedy(
                n_vars, phys_adj, phys_deg, qubits_ids, weight_adj, abs_weight_sum, mapping_pos)) {
            g_last_error = "Failed to build mapping (seeded_neighbor_greedy)";
            return 2;
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double, std::milli> mapping_ms = t1 - t0;
        if (out_mapping_ms) *out_mapping_ms = mapping_ms.count();

        for (int i = 0; i < n_vars; ++i) {
            int qpos = mapping_pos[i];
            int qid = qubits_ids[qpos];
            out_mapping[i] = qid;
        }

        return 0;
    } catch (const std::exception &e) {
        g_last_error = e.what();
        return 3;
    } catch (...) {
        g_last_error = "Unknown error";
        return 4;
    }
}

const char *embed_last_error() {
    return g_last_error.c_str();
}

}  // extern "C"
