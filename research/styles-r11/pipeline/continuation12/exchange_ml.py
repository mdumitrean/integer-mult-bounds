"""Fixed, descriptive historical owner-exchange models; no scientific entrypoint.

The coordinator loads authenticated generation receipts once in the parent and
dispatches every task through pipeline/pool.py.  No fetched program is imported.
All model choices below are fixed before data generation.  A complete guard
oracle is the label definition, not a learned competitor or a kappa claim.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


PKG = Path(__file__).resolve().parents[2]
CORPUS_SEED = 120071
MODELS = ("core_linear", "core_quadratic", "mechanism_linear", "mechanism_quadratic")
SPLITS = ("whole_fill", "joint_endpoint_disjoint", "exact_pair_purged")
CAPS = (512, 2048, 8192, 32768, 131072)
PROTOCOL = {
    "schema": "styles-r11-historical-exchange-ml/v1",
    "inferential_status": "DESCRIPTIVE_ONLY",
    "sources": ["2853", "2917", "2979"],
    "corpus_seed": CORPUS_SEED,
    "execution_seeds": [61001, 122011],
    "target": "legal AND gain_sign==+1; strict exact complete-profile improvement, not kappa admission",
    "models": list(MODELS),
    "splits": list(SPLITS),
    "training_cap": 131072,
    "heldout_cap": 131072,
    "learning_curve_caps": list(CAPS),
    "benchmark_panel_per_fill": 8192,
    "permutations_per_seed": 2000,
    "penalty": {"type": "L2", "lambda": 0.1, "intercept_penalized": False},
    "optimizer": {"method": "L-BFGS-B", "maxiter": 80, "ftol": 1e-10, "gtol": 1e-7, "maxls": 30},
    "features": "core rank/price-free columns; optional six width/residual/capacity columns explicitly cost-derived",
    "preprocessing": "train-only inverse-inclusion-weighted means/scales; clip standardized x to [-8,8]; quadratic appends x*x; no feature selection",
    "training_weights": "inverse inclusion and label-blind subsampling; balance each class to one half for fitting; restore training population-prior log odds at prediction",
    "subsampling": "label-blind fixed salted SplitMix64 pair hash, choose smallest hashes; include exact N/n retention factor; no adaptive cap",
    "joint_split": "same global salted hash namespace for call IDs and physical-family IDs; train all four endpoints in side0, test all four in side1; discard mixed rows",
    "pair_purge": "remove from other-fill training every canonical role pair present anywhere in held-out fill before sampling; report degeneration",
    "metrics": ["weighted_AUROC", "weighted_average_precision", "weighted_Brier", "weighted_logloss", "population_and_conditional_S", "sample_top100_1000_10000"],
    "baselines": ["training_population_mean", "training_prevalence_within_S_and_zero_outside_cost_derived", "capacity_and_positive_spread_and_reciprocal_windows", "complete_exact_guard_oracle_equals_target"],
    "permutation_null": "Within each fixed source-fill x S-flag benchmark-panel block, shuffle exact binary labels, keeping pairs/features/weights and block class counts fixed. One-class blocks unchanged. Tests conditional within-block feature-label association in this finite related lineage only.",
    "permutation_statistic": "mean over three held-out fills of weighted Brier(training mean)-weighted Brier(model), separately core_linear/core_quadratic",
    "permutation_secondary_statistic": "same Brier difference against train-within-S prevalence and zero outsideS; guards against credit merely for identifying the necessary-gain stratum",
    "permutation_reporting": "unshuffled matched benchmark and 2000 indexed shuffle statistics; no p/q, pattern, independence, causal or best-model claim",
    "relatedness": "Three allocations share ancestry; entire-fill holdout is a sensitivity, not independent replication.",
    "no_adaptive_tuning": True,
}
_STATE = {}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _source(value):
    s = str(value).lower().removeprefix("pr").removeprefix("#")
    if s not in PROTOCOL["sources"]:
        raise ValueError("unexpected source " + s)
    return s


def _path(value):
    p = Path(value)
    if not p.is_absolute():
        p = (PKG / p) if not str(p).startswith("research/styles-r11/") else PKG.parents[1] / p
    p = p.resolve()
    if not p.is_relative_to(PKG):
        raise ValueError("artifact outside r11")
    return p


def _bytes(ref):
    p = _path(ref["path"])
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != ref["sha256"]:
        raise ValueError("artifact hash mismatch: " + str(p))
    return b


def _receipt(record):
    if "path" in record and "sha256" in record and "artifact" not in record:
        b = _bytes(record)
        record = json.loads(gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b)
    if "item" in record:
        record = record["item"]
    if "result" in record:
        if record.get("status") != "OK":
            raise ValueError("generation pool receipt was not OK")
        record = record["result"]
    return record


def _hash64(x, salt):
    # Fixed integer permutation, independent of all observed labels/features.
    x = np.asarray(x, dtype=np.uint64).copy()
    with np.errstate(over="ignore"):
        x += np.uint64(salt)
        x ^= x >> np.uint64(30)
        x *= np.uint64(0xBF58476D1CE4E5B9)
        x ^= x >> np.uint64(27)
        x *= np.uint64(0x94D049BB133111EB)
        x ^= x >> np.uint64(31)
    return x


def _salt(text):
    return int.from_bytes(hashlib.sha256((str(CORPUS_SEED) + ":" + text).encode()).digest()[:8], "little")


def _keys(pairs):
    return (pairs[:, 0].astype(np.uint64) << np.uint64(32)) | pairs[:, 1].astype(np.uint64)


def _take(ids, keys, cap, salt):
    """Uniform-size, label-blind hash panel; nested for a fixed salt."""
    ids = np.asarray(ids, dtype=np.int64)
    n = len(ids)
    if not n:
        return ids, 1.0
    h = _hash64(keys[ids], salt)
    if n > cap:
        chosen = np.argpartition(h, cap - 1)[:cap]
        ids, h = ids[chosen], h[chosen]
    order = np.lexsort((keys[ids], h))
    return ids[order], n / len(ids)


def _panel_record(data, ids, factor, domain_n, design_probability=None):
    return {"rows": len(ids), "domain_rows": int(domain_n), "retention_probability": design_probability or (f"{len(ids)}/{domain_n}" if domain_n else None),
            "inverse_retention_factor": factor, "pair_ids_sha256": hashlib.sha256(data["pairs"][ids].astype("<i4", copy=False).tobytes()).hexdigest()}


def estimate_preparation(generation_receipts):
    """Metadata only: read authenticated receipt JSON, never the numeric NPZ."""
    seen, source_rows = {}, {s: 0 for s in PROTOCOL["sources"]}
    originals = 0
    largest_shard = largest_compressed = 0
    for reference in generation_receipts:
        r = _receipt(reference)
        key = (_source(r["source"]), int(r["shard"]))
        if key in seen:
            if seen[key] != r["semantic_digest"]:
                raise ValueError("generation seeds disagree")
            continue
        seen[key] = r["semantic_digest"]
        schema = r["array_schema"]
        n = int(schema["pairs"]["shape"][0])
        size = 0
        for name in ("pairs", "core_features", "mechanism_features", "labels", "groups", "baseline"):
            item = schema[name]
            shape = tuple(map(int, item["shape"]))
            if len(shape) != 2 or shape[0] != n:
                raise ValueError("inconsistent array metadata")
            dtype = np.dtype(item["dtype"])
            if dtype.kind not in "iu":
                raise ValueError("unexpected array metadata dtype")
            size += shape[0] * shape[1] * dtype.itemsize
        originals += size
        source_rows[key[0]] += n
        largest_shard = max(largest_shard, size)
        largest_compressed = max(largest_compressed, int(r["artifact"]["bytes"]))
    if sorted(seen) != [(s, j) for s in PROTOCOL["sources"] for j in range(84)]:
        raise ValueError("incomplete preparation estimate inventory")
    rows = sum(source_rows.values())
    aux = 28 * rows  # keys8+y1+S1+weight8+cheap8+side0/1 each1.
    base_transient = 2 * originals + aux
    workspace = 32 * max(source_rows.values()) + 2 * largest_shard + 2 * largest_compressed + 64 * 2**20
    return {"status": "ESTIMATE_FROM_AUTHENTICATED_METADATA", "rows": rows, "source_rows": source_rows,
            "original_array_bytes": originals, "auxiliary_bytes_per_row": 28, "auxiliary_array_bytes": aux,
            "predicted_retained_array_bytes": originals + aux,
            "two_copies_plus_auxiliary_bytes": base_transient,
            "additional_sort_hash_decode_and_bookkeeping_allowance_bytes": workspace,
            "predicted_transient_upper_bound_bytes": base_transient + workspace,
            "scope": "Incremental model-array estimate; coordinator adds current parent RSS and pool projection. No NPZ contents loaded by this function."}


def prepare(generation_receipts, protocol=None):
    """Load only authenticated NPZ data, once in the parent; never call dataset code."""
    global _STATE
    if _STATE:
        raise RuntimeError("model prepare must run once per parent")
    if protocol is not None:
        supplied = protocol.get("model_protocol", protocol)
        for k in ("training_cap", "heldout_cap", "benchmark_panel_per_fill", "permutations_per_seed"):
            if k in supplied and supplied[k] != PROTOCOL[k]:
                raise ValueError("unregistered model parameter " + k)
    chunks = {s: [] for s in PROTOCOL["sources"]}
    seen = {}
    refs = []
    schema = None
    from io import BytesIO
    for reference in generation_receipts:
        r = _receipt(reference)
        s = _source(r["source"])
        shard = int(r["shard"])
        semantic = r["semantic_digest"]
        if (s, shard) in seen:
            if seen[s, shard] != semantic:
                raise ValueError("two execution seeds disagree on corpus")
            continue
        seen[s, shard] = semantic
        sch = r["feature_schema"]
        if schema is None:
            schema = sch
        if sch != schema:
            raise ValueError("feature schemas differ")
        sampling = r["sampling"]
        if int(sampling["D"]) != 36862620480 or int(sampling["n"]) != 1048576:
            raise ValueError("unregistered design sampling")
        b = _bytes(r["artifact"])
        with np.load(BytesIO(b), allow_pickle=False) as z:
            a = {k: z[k].copy() for k in ("pairs", "core_features", "mechanism_features", "labels", "groups", "baseline")}
        n = len(a["pairs"])
        for k, width in (("pairs", 2), ("mechanism_features", 6), ("labels", 4), ("groups", 6), ("baseline", 4)):
            if a[k].shape != (n, width) or a[k].dtype.kind not in "iu":
                raise ValueError("bad data array " + k)
        if a["core_features"].shape[0] != n or a["core_features"].ndim != 2 or a["core_features"].dtype.kind not in "iu":
            raise ValueError("bad core feature array")
        if a["core_features"].shape[1] != len(sch["core"]) or len(sch["core"]) != 23 or len(sch["mechanism"]) != 6:
            raise ValueError("registered feature columns")
        if np.any(a["pairs"][:, 0] >= a["pairs"][:, 1]):
            raise ValueError("noncanonical pair")
        if not np.isin(a["labels"][:, 0], [0, 1]).all() or not np.isin(a["labels"][:, 1], [-1, 0, 1]).all() or not np.isin(a["labels"][:, 2:], [0, 1]).all():
            raise ValueError("bad target flags")
        chunks[s].append((shard, a))
        refs.append({"source": s, "shard": shard, "artifact": r["artifact"], "semantic_digest": semantic})
    fills = {}
    panels = {}
    total_bytes = 0
    for s, items in chunks.items():
        if sorted(x[0] for x in items) != list(range(84)):
            raise ValueError("incomplete generation shards " + s)
        items.sort(key=lambda t: t[0])
        a = {k: np.concatenate([x[k] for _, x in items], axis=0) for k in items[0][1]}
        if len(a["pairs"]) > 2000000:
            raise ValueError("registered corpus row cap")
        a["keys"] = _keys(a["pairs"])
        if len(np.unique(a["keys"])) != len(a["keys"]):
            raise ValueError("duplicate corpus pair")
        a["y"] = ((a["labels"][:, 0] == 1) & (a["labels"][:, 1] == 1)).astype(np.int8)
        a["S"] = a["labels"][:, 2].astype(bool)
        if np.any(a["y"] & ~a["S"]):
            raise ValueError("positive outside necessary-gain stratum")
        a["weight"] = np.where(a["S"], 1.0, 36862620480 / 1048576)
        a["cheap"] = np.all(a["baseline"][:, :3] > 0, axis=1).astype(np.float64)
        g = a["groups"]
        a["side0"] = np.ones(len(g), dtype=bool)
        a["side1"] = np.ones(len(g), dtype=bool)
        for j in range(4):
            side = _hash64(g[:, j], _salt("call" if j < 2 else "physical_family")) & np.uint64(1)
            a["side0"] &= side == 0
            a["side1"] &= side == 1
        for val in a.values():
            val.flags.writeable = False
            total_bytes += val.nbytes
        fills[s] = a
        ids, factor = _take(np.arange(len(a["y"])), a["keys"], 8192, _salt("benchmark:" + s))
        panels[s] = (ids, factor)
    _STATE = {"fills": fills, "panels": panels, "schema": schema, "receipts": refs,
              "corpus_digest": digest(refs), "array_bytes": total_bytes}
    return {"status": "PREPARED", "scope": "parent-only authenticated dataset load", "protocol": PROTOCOL,
            "protocol_sha256": digest(PROTOCOL), "corpus_sha256": _STATE["corpus_digest"], "array_bytes": total_bytes,
            "rows": {s: len(a["y"]) for s, a in fills.items()},
            "benchmark_panels": {s: _panel_record(fills[s], *panels[s], len(fills[s]["y"])) for s in fills},
            "feature_schema": schema}


def observed_specs(seed):
    return [{"kind": "observed", "seed": int(seed), "holdout": s, "model": m, "split": split, "train_cap": 131072}
            for s in PROTOCOL["sources"] for m in MODELS for split in SPLITS]


def learning_curve_specs(seed):
    return [{"kind": "learning_curve", "seed": int(seed), "holdout": s, "model": m, "split": "whole_fill", "train_cap": cap}
            for s in PROTOCOL["sources"] for m in MODELS for cap in CAPS]


def benchmark_specs(seed):
    return [{"kind": "benchmark", "seed": int(seed), "permutation": None}]


def permutation_specs(seed, n=2000):
    if n != 2000:
        raise ValueError("registered benchmark count is 2000")
    return [{"kind": "permutation", "seed": int(seed), "permutation": i} for i in range(n)]


def model_specs(seed):
    return observed_specs(seed) + learning_curve_specs(seed) + benchmark_specs(seed) + permutation_specs(seed)


def _features(a, ids, model):
    x = a["core_features"][ids].astype(np.float64)
    if model.startswith("mechanism"):
        x = np.concatenate((x, a["mechanism_features"][ids]), axis=1)
    return x


def _standardizer(x, w):
    w = w / w.sum()
    mean = w @ x
    var = w @ ((x - mean) ** 2)
    scale = np.sqrt(np.maximum(var, 0.0))
    scale[scale < 1e-12] = 1.0
    return mean, scale


def _transform(x, mean, scale, model):
    z = np.clip((x - mean) / scale, -8.0, 8.0)
    return np.concatenate((z, z * z), axis=1) if model.endswith("quadratic") else z


def _fit(x, y, w, model):
    if not len(y) or w.sum() <= 0:
        return {"status": "UNIDENTIFIABLE_EMPTY_TRAIN", "prior": None}
    prior = float(w @ y / w.sum())
    if prior <= 0 or prior >= 1:
        return {"status": "UNIDENTIFIABLE_ONE_CLASS", "prior": prior, "converged": None}
    mean, scale = _standardizer(x, w)
    z = _transform(x, mean, scale, model)
    positive = float(w @ y)
    negative = float(w @ (1 - y))
    balanced = w / np.where(y == 1, 2 * positive, 2 * negative)
    def objective(beta):
        score = z @ beta[1:] + beta[0]
        loss = float(balanced @ (np.logaddexp(0.0, score) - y * score) + 0.05 * (beta[1:] @ beta[1:]))
        residual = balanced * (expit(score) - y)
        grad = np.concatenate(([residual.sum()], z.T @ residual + 0.1 * beta[1:]))
        return loss, grad
    opt = minimize(objective, np.zeros(z.shape[1] + 1), method="L-BFGS-B", jac=True,
                   options={k: v for k, v in PROTOCOL["optimizer"].items() if k != "method"})
    return {"status": "FIT" if opt.success else "OPTIMIZER_NOT_CONVERGED", "prior": prior, "mean": mean, "scale": scale,
            "beta": opt.x, "prior_logodds": float(np.log(prior) - np.log1p(-prior)), "converged": bool(opt.success),
            "iterations": int(opt.nit), "objective": float(opt.fun), "message": str(opt.message)}


def _predict(fit, x, model):
    if fit["prior"] is None:
        return None
    if "beta" not in fit:
        return np.full(len(x), fit["prior"])
    z = _transform(x, fit["mean"], fit["scale"], model)
    return expit(z @ fit["beta"][1:] + fit["beta"][0] + fit["prior_logodds"])


def _metrics(y, p, w, pairs=None, ranking=True):
    n = len(y)
    if not n or float(w.sum()) <= 0:
        return {"status": "UNIDENTIFIABLE_EMPTY_EVALUATION", "rows": int(n)}
    total, pos = float(w.sum()), float(w @ y)
    prevalence = pos / total
    clip = np.clip(p, 1e-15, 1 - 1e-15)
    out = {"status": "MEASURED", "rows": int(n), "positive_rows": int(y.sum()), "weight_sum": total,
           "weighted_positive_sum": pos, "weighted_prevalence": prevalence,
           "Brier": float(w @ ((p - y) ** 2) / total),
           "logloss": float(-w @ (y * np.log(clip) + (1 - y) * np.log1p(-clip)) / total)}
    if pos == 0 or pos == total:
        out.update(AUROC=None, average_precision=None, ranking_status="UNIDENTIFIABLE_ONE_CLASS")
    else:
        order = np.argsort(-p, kind="stable")
        scores, wy, wn = p[order], (w * y)[order], (w * (1 - y))[order]
        ends = np.r_[np.flatnonzero(scores[1:] != scores[:-1]) + 1, n]
        cp, cn = np.cumsum(wy), np.cumsum(wn)
        tp, fp = cp[ends - 1], cn[ends - 1]
        dp = np.diff(np.r_[0.0, tp])
        out["average_precision"] = float(np.sum((dp / pos) * (tp / (tp + fp))))
        out["AUROC"] = float(np.sum(np.diff(np.r_[0.0, fp]) * (np.r_[0.0, tp[:-1]] + tp) / 2) / (pos * (total - pos)))
        out["ranking_status"] = "TIE_GROUPED"
    if ranking:
        if pairs is None:
            order = np.argsort(-p, kind="stable")
        else:
            order = np.lexsort((pairs[:, 1], pairs[:, 0], -p))
        top = {}
        for k in (100, 1000, 10000):
            take = order[:min(n, k)]
            top[str(k)] = {"rows": len(take), "positives": int(y[take].sum()),
                           "precision": float(y[take].mean()) if len(take) else None,
                           "recall": float(y[take].sum() / y.sum()) if y.sum() else None}
        out["sample_top_k"] = top
        out["top_k_scope"] = "unweighted selected evaluation sample; not population topK"
    return out


def _indices(holdout, split, cap):
    fills = _STATE["fills"]
    test = fills[holdout]
    all_test = np.arange(len(test["y"]))
    eligible_test = all_test[test["side1"]] if split == "joint_endpoint_disjoint" else all_test
    test_ids, test_factor = _take(eligible_test, test["keys"], 131072, _salt("evaluation:" + holdout + ":" + split))
    train = []
    domain = []
    for s, a in fills.items():
        if s == holdout:
            continue
        ids = np.arange(len(a["y"]))
        if split == "joint_endpoint_disjoint":
            ids = ids[a["side0"]]
        elif split == "exact_pair_purged":
            ids = ids[~np.isin(a["keys"][ids], test["keys"], assume_unique=True)]
        domain.append((s, ids))
    # Uniform-size sample across both eligible training fills, using an explicit
    # source salt so identical pair IDs in distinct fills remain distinct units.
    all_h = np.concatenate([_hash64(fills[s]["keys"][ids], _salt("train:" + holdout + ":" + split + ":" + s)) for s, ids in domain])
    N = len(all_h)
    chosen = np.argpartition(all_h, cap - 1)[:cap] if N > cap else np.arange(N)
    chosen = chosen[np.argsort(all_h[chosen], kind="stable")]
    offset = 0
    factor = N / len(chosen) if len(chosen) else 1.0
    for s, ids in domain:
        sel = chosen[(chosen >= offset) & (chosen < offset + len(ids))] - offset
        train.append((s, ids[sel], factor, len(ids)))
        offset += len(ids)
    return train, (test_ids, test_factor, len(eligible_test))


def _one_fit(spec):
    holdout, model, split = _source(spec["holdout"]), spec["model"], spec["split"]
    cap = int(spec["train_cap"])
    if model not in MODELS or split not in SPLITS or cap not in CAPS:
        raise ValueError("unregistered model task")
    train, (test_ids, factor, domain_n) = _indices(holdout, split, cap)
    fills = _STATE["fills"]
    train_n = sum(len(ids) for _, ids, _, _ in train)
    train_N = sum(n for _, _, _, n in train)
    x = np.concatenate([_features(fills[s], ids, model) for s, ids, _, _ in train])
    y = np.concatenate([fills[s]["y"][ids] for s, ids, _, _ in train])
    w = np.concatenate([fills[s]["weight"][ids] * f for s, ids, f, _ in train])
    train_s = np.concatenate([fills[s]["S"][ids] for s, ids, _, _ in train])
    prior_s = float(w[train_s] @ y[train_s] / w[train_s].sum()) if train_s.any() else None
    fit = _fit(x, y, w, model)
    test = fills[holdout]
    prediction = _predict(fit, _features(test, test_ids, model), model)
    out = {"status": "EXPLORATORY", "kind": spec["kind"], "seed": int(spec["seed"]), "holdout": holdout,
           "model": model, "split": split, "train_cap": cap, "fit_status": fit["status"],
           "training": {s: _panel_record(fills[s], ids, f, n, f"{train_n}/{train_N}" if train_N else None) for s, ids, f, n in train},
           "evaluation": _panel_record(test, test_ids, factor, domain_n), "training_positive_rows": int(y.sum()),
           "training_population_prior": fit["prior"], "training_S_prior": prior_s,
           "optimizer": {k: fit[k] for k in ("converged", "iterations", "objective", "message") if k in fit},
           "mechanism_features_used": model.startswith("mechanism"), "corpus_sha256": _STATE["corpus_digest"]}
    if prediction is None or not len(test_ids):
        out["metrics"] = None
        if not len(test_ids):
            out["evaluation_status"] = "UNIDENTIFIABLE_EMPTY_EVALUATION"
        return out
    yy, ww, ss = test["y"][test_ids], test["weight"][test_ids] * factor, test["S"][test_ids]
    out["metrics"] = {}
    predictions = [("model", prediction), ("training_mean", np.full(len(yy), fit["prior"])),
                   ("cheap_exact_screen", test["cheap"][test_ids]), ("complete_oracle_definition", yy.astype(float))]
    if prior_s is not None:
        predictions.append(("training_stratum_mean", np.where(ss, prior_s, 0.0)))
    else:
        out["stratum_mean_status"] = "UNIDENTIFIABLE_NO_TRAINING_S_ROWS"
    for name, pred in predictions:
        out["metrics"][name] = {"population": _metrics(yy, pred, ww, test["pairs"][test_ids]),
                               "conditional_S": _metrics(yy[ss], pred[ss], ww[ss], test["pairs"][test_ids][ss])}
    out["Brier_improvement_over_mean"] = out["metrics"]["training_mean"]["population"]["Brier"] - out["metrics"]["model"]["population"]["Brier"]
    out["Brier_improvement_over_stratum_mean"] = (out["metrics"]["training_stratum_mean"]["population"]["Brier"] - out["metrics"]["model"]["population"]["Brier"]) if prior_s is not None else None
    if "beta" in fit:
        out["fitted_parameters"] = {"mean": fit["mean"].tolist(), "scale": fit["scale"].tolist(), "beta": fit["beta"].tolist(), "population_prior_logodds": fit["prior_logodds"]}
    return out


def _shuffle_labels(y, strata, seed):
    rng = np.random.default_rng(seed)
    out = y.copy()
    detail = []
    for flag in (False, True):
        ids = np.flatnonzero(strata == flag)
        positives = int(y[ids].sum())
        movable = 0 < positives < len(ids)
        if movable:
            out[ids] = y[ids][rng.permutation(len(ids))]
        detail.append({"S": flag, "rows": len(ids), "positives": positives, "movable": movable})
    return out, detail


def _benchmark(spec):
    perm = spec.get("permutation")
    if perm is not None and not 0 <= int(perm) < 2000:
        raise ValueError("unregistered permutation")
    fills, panels = _STATE["fills"], _STATE["panels"]
    labels, blocks = {}, {}
    for s in PROTOCOL["sources"]:
        ids, _ = panels[s]
        a = fills[s]
        if perm is None:
            labels[s] = a["y"][ids]
            _, blocks[s] = _shuffle_labels(labels[s], a["S"][ids], 0)
        else:
            seed = int.from_bytes(hashlib.sha256(f"{spec['seed']}:{perm}:{s}".encode()).digest()[:8], "little")
            labels[s], blocks[s] = _shuffle_labels(a["y"][ids], a["S"][ids], seed)
    records = []
    for holdout in PROTOCOL["sources"]:
        for model in ("core_linear", "core_quadratic"):
            tr = [s for s in PROTOCOL["sources"] if s != holdout]
            x = np.concatenate([_features(fills[s], panels[s][0], model) for s in tr])
            y = np.concatenate([labels[s] for s in tr])
            w = np.concatenate([fills[s]["weight"][panels[s][0]] * panels[s][1] for s in tr])
            train_s = np.concatenate([fills[s]["S"][panels[s][0]] for s in tr])
            prior_s = float(w[train_s] @ y[train_s] / w[train_s].sum()) if train_s.any() else None
            fit = _fit(x, y, w, model)
            ids, factor = panels[holdout]
            a = fills[holdout]
            pred = _predict(fit, _features(a, ids, model), model)
            rec = {"holdout": holdout, "model": model, "fit_status": fit["status"], "converged": fit.get("converged"),
                   "training_prior": fit["prior"], "training_S_prior": prior_s,
                   "Brier_improvement_over_mean": None, "Brier_improvement_over_stratum_mean": None}
            if pred is not None:
                yy, ww = labels[holdout], a["weight"][ids] * factor
                brier = float(ww @ ((pred - yy) ** 2) / ww.sum())
                base = float(ww @ ((fit["prior"] - yy) ** 2) / ww.sum())
                ss = a["S"][ids]
                stratum_brier = float(ww @ ((np.where(ss, prior_s, 0.0) - yy) ** 2) / ww.sum()) if prior_s is not None else None
                rec.update(Brier=brier, mean_Brier=base, Brier_improvement_over_mean=base - brier,
                           stratum_mean_Brier=stratum_brier,
                           Brier_improvement_over_stratum_mean=stratum_brier - brier if stratum_brier is not None else None,
                           conditional_S_Brier=float(ww[ss] @ ((pred[ss] - yy[ss]) ** 2) / ww[ss].sum()) if ss.any() else None)
            records.append(rec)
    movable_blocks = sum(b["movable"] for values in blocks.values() for b in values)
    stats, secondary = {}, {}
    for model in ("core_linear", "core_quadratic"):
        vals = [r["Brier_improvement_over_mean"] for r in records if r["model"] == model]
        stats[model] = float(np.mean(vals)) if movable_blocks and all(v is not None for v in vals) else None
        other = [r["Brier_improvement_over_stratum_mean"] for r in records if r["model"] == model]
        secondary[model] = float(np.mean(other)) if movable_blocks and all(v is not None for v in other) else None
    return {"status": "EXPLORATORY", "kind": spec["kind"], "seed": int(spec["seed"]), "permutation": perm,
            "statistics": stats, "secondary_statistics": secondary, "folds": records, "blocks": blocks,
            "movable_blocks": movable_blocks, "fixed_one_class_blocks": 6 - movable_blocks,
            "identification": "CONDITIONAL_SHUFFLE_AVAILABLE" if movable_blocks else "UNIDENTIFIABLE_ALL_BLOCKS_ONE_CLASS",
            "permuted_labels_sha256": {s: hashlib.sha256(labels[s].tobytes()).hexdigest() for s in labels},
            "panels": {s: _panel_record(fills[s], *panels[s], len(fills[s]["y"])) for s in fills},
            "corpus_sha256": _STATE["corpus_digest"], "inferential_status": "DESCRIPTIVE_ONLY_NO_P_OR_Q"}


def task(spec):
    if not _STATE:
        raise RuntimeError("prepare in parent first")
    if int(spec["seed"]) not in PROTOCOL["execution_seeds"]:
        raise ValueError("unregistered execution seed")
    if spec["kind"] in ("observed", "learning_curve"):
        return _one_fit(spec)
    if spec["kind"] in ("benchmark", "permutation"):
        return _benchmark(spec)
    raise ValueError("unregistered model task kind")


def controls(seed):
    """Small mathematical/metamorphic controls, run only by the central pool."""
    checks = []
    def check(name, good):
        if not good:
            raise AssertionError(name)
        checks.append(name)
    y = np.array([0, 0, 1, 1], dtype=np.int8)
    w = np.array([2., 1., 1., 2.])
    good = _metrics(y, y.astype(float), w)
    check("perfect weighted ranking", good["AUROC"] == 1 and good["Brier"] == 0 and good["average_precision"] == 1)
    tied = _metrics(y, np.full(4, .5), w)
    check("tied weighted ranking", abs(tied["AUROC"] - .5) < 1e-14 and abs(tied["average_precision"] - .5) < 1e-14)
    reverse = _metrics(y, 1 - y.astype(float), w)
    check("reverse weighted ranking", reverse["AUROC"] == 0)
    check("one class explicitly unavailable", _metrics(np.zeros(4), np.zeros(4), w)["AUROC"] is None)
    x = np.zeros((100, 3)); yy = np.r_[np.zeros(90), np.ones(10)].astype(np.int8)
    fit = _fit(x, yy, np.ones(100), "core_linear")
    check("balanced fit restores population prior", np.max(np.abs(_predict(fit, x, "core_linear") - .1)) < 1e-7)
    fit2 = _fit(x, yy, np.ones(100), "core_quadratic")
    check("quadratic constant restores prior", np.max(np.abs(_predict(fit2, x, "core_quadratic") - .1)) < 1e-7)
    mean, scale = _standardizer(np.array([[0., 1.], [2., 1.]]), np.ones(2))
    check("constant feature scale", np.array_equal(mean, [1, 1]) and np.array_equal(scale, [1, 1]))
    _transform(np.array([[1e12, -1e12]]), mean, scale, "core_quadratic")
    check("test transform cannot fit moments", np.array_equal(mean, [1, 1]) and np.array_equal(scale, [1, 1]))
    strata = np.array([False] * 50 + [True] * 50)
    shuffled, blocks = _shuffle_labels(yy, strata, int(seed))
    check("matched shuffle preserves every block count", all(int(shuffled[strata == b['S']].sum()) == b["positives"] for b in blocks))
    check("one-class block unchanged", np.array_equal(shuffled[:50], yy[:50]))
    pairs = np.column_stack((np.arange(100), np.arange(100) + 101)).astype(np.int32)
    keys = _keys(pairs)
    p10, factor = _take(np.arange(100), keys, 10, _salt("control"))
    p20, _ = _take(np.arange(100), keys, 20, _salt("control"))
    check("nested label-blind caps", set(p10).issubset(set(p20)) and factor == 10)
    check("complete exact oracle is label definition", np.array_equal(((np.array([1, 0, 1]) == 1) & (np.array([1, 1, -1]) == 1)), [True, False, False]))
    check("spec coverage", len(observed_specs(seed)) == 36 and len(learning_curve_specs(seed)) == 60 and len(benchmark_specs(seed)) == 1 and len(permutation_specs(seed)) == 2000)
    return {"status": "PASS", "seed": int(seed), "checks": checks, "count": len(checks), "protocol_sha256": digest(PROTOCOL)}


def feature_schema():
    return _STATE.get("schema")


def get_state():
    return {"prepared": bool(_STATE), "array_bytes": _STATE.get("array_bytes"), "corpus_sha256": _STATE.get("corpus_digest")}


def _summaries(observed):
    for phase, records in observed.items():
        for record in records:
            item = record.get("summary", record.get("result", record))
            if isinstance(item, dict):
                yield phase, item


def _compact_fit(row):
    out = {k: row[k] for k in ("holdout", "model", "split", "train_cap", "fit_status", "training_positive_rows", "training_population_prior", "training_S_prior")}
    out["Brier_improvement_over_mean"] = row.get("Brier_improvement_over_mean")
    out["Brier_improvement_over_stratum_mean"] = row.get("Brier_improvement_over_stratum_mean")
    out["evaluation_rows"] = row["evaluation"]["rows"]
    out["metrics"] = None
    if row.get("metrics"):
        out["metrics"] = {
            model: {scope: {k: v for k, v in stats.items() if k in ("status", "rows", "positive_rows", "weighted_prevalence", "Brier", "logloss", "AUROC", "average_precision")}
                    for scope, stats in scopes.items()}
            for model, scopes in row["metrics"].items() if model in ("model", "training_mean", "training_stratum_mean", "cheap_exact_screen")}
    out["full_task_result_sha256"] = digest(row)
    return out


def summarize(observed, protocol=None):
    """Compact descriptive aggregation; deliberately no p/q or pattern verdict."""
    by_seed = {str(s): [] for s in PROTOCOL["execution_seeds"]}
    for _, item in _summaries(observed):
        if item.get("kind") in ("observed", "learning_curve", "benchmark", "permutation"):
            by_seed[str(item["seed"])].append(item)
    decisions = {}
    repeat_hashes = {}
    for seed, items in by_seed.items():
        groups = {k: [x for x in items if x["kind"] == k] for k in ("observed", "learning_curve", "benchmark", "permutation")}
        expected = {"observed": 36, "learning_curve": 60, "benchmark": 1, "permutation": 2000}
        if {k: len(v) for k, v in groups.items()} != expected:
            raise ValueError("incomplete descriptive ML inventory " + seed)
        for kind in ("observed", "learning_curve"):
            keys = [(r["holdout"], r["model"], r["split"], r["train_cap"]) for r in groups[kind]]
            if len(set(keys)) != len(keys):
                raise ValueError("duplicate model task")
        if sorted(x["permutation"] for x in groups["permutation"]) != list(range(2000)):
            raise ValueError("incomplete permutation index set")
        repeated = [{k: v for k, v in row.items() if k != "seed"} for row in groups["observed"] + groups["learning_curve"] + groups["benchmark"]]
        repeated.sort(key=lambda x: (x["kind"], x.get("holdout", ""), x.get("model", ""), x.get("split", ""), x.get("train_cap", 0)))
        repeat_hashes[seed] = digest(repeated)
        shuffle = {}
        for model in ("core_linear", "core_quadratic"):
            vals = [r["statistics"][model] for r in groups["permutation"] if r["statistics"][model] is not None]
            shuffle[model] = {"identified": len(vals), "unidentified": 2000 - len(vals),
                              "mean": float(np.mean(vals)) if vals else None,
                              "quantiles_0_025_50_975_100": np.quantile(vals, [0, .025, .5, .975, 1]).tolist() if vals else None,
                              "observed_matched_panel_statistic": groups["benchmark"][0]["statistics"][model]}
            secondary = [r["secondary_statistics"][model] for r in groups["permutation"] if r["secondary_statistics"][model] is not None]
            shuffle[model]["secondary_stratum_mean"] = {
                "identified": len(secondary), "unidentified": 2000 - len(secondary),
                "mean": float(np.mean(secondary)) if secondary else None,
                "quantiles_0_025_50_975_100": np.quantile(secondary, [0, .025, .5, .975, 1]).tolist() if secondary else None,
                "observed_matched_panel_statistic": groups["benchmark"][0]["secondary_statistics"][model]}
        decisions[seed] = {"status": "EXPLORATORY", "inferential_status": "DESCRIPTIVE_ONLY_NO_P_OR_Q", "task_counts": expected,
                           "observed": [_compact_fit(x) for x in groups["observed"]], "learning_curves": [_compact_fit(x) for x in groups["learning_curve"]],
                           "matched_benchmark": groups["benchmark"][0], "shuffle_benchmarks": shuffle,
                           "deterministic_results_sha256": repeat_hashes[seed],
                           "fit_nonconvergence_count": sum(x.get("fit_status") == "OPTIMIZER_NOT_CONVERGED" for x in groups["observed"] + groups["learning_curve"]),
                           "permutation_fit_nonconvergence_count": sum(f["fit_status"] == "OPTIMIZER_NOT_CONVERGED" for r in groups["permutation"] for f in r["folds"]),
                           "scope": "Screening association/cost interpretation in related historical allocations; no kappa admission or independent-lineage pattern."}
    return {"status": "EXPLORATORY", "confirmed": len(set(repeat_hashes.values())) == 1,
            "confirmation_scope": "Exact repeated observed models/learning curves/unshuffled benchmark; indexed shuffle labels differ between execution seeds.",
            "seeds": decisions, "protocol_sha256": digest(PROTOCOL), "corpus_sha256": _STATE["corpus_digest"]}
