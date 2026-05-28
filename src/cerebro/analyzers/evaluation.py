"""Objective-aware evaluation metric computation.

Dispatches to the correct panel function based on the model's objective.
All functions are pure over predictions + labels; no LightGBM import at
module level. The booster's predict() output is passed in as numpy arrays.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import structlog
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    ndcg_score,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.schema.v1.evaluation import (
    BinaryEval,
    ConfusionCell,
    HistogramBin,
    IntervalPoint,
    MulticlassEval,
    NDCGAtK,
    PerClassMetrics,
    RankingEval,
    RegressionEval,
    ROCPoint,
    ScatterPoint,
)

log = structlog.get_logger()

RESIDUAL_HISTOGRAM_BINS: int = 30
PREDICTION_INTERVAL_PERCENTILES: tuple[float, float] = (5.0, 95.0)
SCATTER_MAX_POINTS: int = 500
NDCG_K_VALUES: tuple[int, ...] = (1, 3, 5, 10)


def evaluate(
    predictions: np.ndarray,
    labels: np.ndarray,
    objective: str,
    *,
    query_ids: np.ndarray | None = None,
) -> BinaryEval | MulticlassEval | RegressionEval | RankingEval:
    """Dispatch to the correct evaluation panel based on objective.

    Args:
        predictions: Model output array (raw probabilities or scores).
        labels: Ground-truth label array.
        objective: One of "binary", "multiclass", "regression", "lambdarank".
        query_ids: Required for ranking objectives; maps each sample to its query.

    Returns:
        The typed evaluation payload for the artifact.

    Raises:
        UnsupportedObjectiveError: For unknown objective strings.
    """
    if objective == "binary":
        result = _evaluate_binary(predictions, labels)
    elif objective == "multiclass":
        if predictions.ndim == 2:
            n_classes = int(predictions.shape[1])
        else:
            n_classes = len(np.unique(labels))
        result = _evaluate_multiclass(predictions, labels, n_classes)
    elif objective in ("regression", "multi_output"):
        result = _evaluate_regression(predictions, labels)
    elif objective == "lambdarank":
        if query_ids is None:
            raise ValueError("query_ids is required for lambdarank evaluation")
        result = _evaluate_ranking(predictions, labels, query_ids)
    else:
        raise UnsupportedObjectiveError(
            f"evaluation not supported for objective {objective!r}",
            context={"objective": objective},
        )

    log.info("evaluation.computed", objective=objective)
    return result


# ---------------------------------------------------------------------------
# Binary
# ---------------------------------------------------------------------------


def _evaluate_binary(predictions: np.ndarray, labels: np.ndarray) -> BinaryEval:
    probs = predictions.ravel()
    hard = (probs >= 0.5).astype(int)

    auc = float(roc_auc_score(labels, probs))
    fpr_arr, tpr_arr, thresh_arr = roc_curve(labels, probs)
    roc_points = [
        ROCPoint(fpr=float(f), tpr=float(t), threshold=float(th))
        for f, t, th in zip(fpr_arr, tpr_arr, thresh_arr, strict=False)
    ]

    cm = confusion_matrix(labels, hard)
    cm_cells = _cm_to_cells(cm)

    return BinaryEval(
        objective="binary",
        auc=auc,
        roc_curve=roc_points,
        confusion_matrix=cm_cells,
        threshold=0.5,
        precision=float(precision_score(labels, hard, zero_division=0)),
        recall=float(recall_score(labels, hard, zero_division=0)),
        f1=float(f1_score(labels, hard, zero_division=0)),
    )


# ---------------------------------------------------------------------------
# Multiclass
# ---------------------------------------------------------------------------


def _evaluate_multiclass(
    predictions: np.ndarray, labels: np.ndarray, n_classes: int
) -> MulticlassEval:
    if predictions.ndim == 2:
        hard = predictions.argmax(axis=1)
    else:
        hard = predictions.astype(int)

    cm = confusion_matrix(labels, hard, labels=list(range(n_classes)))
    cm_cells = _cm_to_cells(cm)

    per_class: list[PerClassMetrics] = []
    cls_labels = list(range(n_classes))
    kw = {"average": None, "zero_division": 0, "labels": cls_labels}
    precs = precision_score(labels, hard, **kw)
    recs = recall_score(labels, hard, **kw)
    f1s = f1_score(labels, hard, **kw)

    for cls_idx in range(n_classes):
        support = int((labels == cls_idx).sum())
        per_class.append(
            PerClassMetrics(
                class_index=cls_idx,
                precision=float(precs[cls_idx]),
                recall=float(recs[cls_idx]),
                f1=float(f1s[cls_idx]),
                support=support,
            )
        )

    return MulticlassEval(
        objective="multiclass",
        confusion_matrix=cm_cells,
        per_class=per_class,
        macro_f1=float(f1_score(labels, hard, average="macro", zero_division=0)),
        accuracy=float(accuracy_score(labels, hard)),
    )


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def _evaluate_regression(predictions: np.ndarray, labels: np.ndarray) -> RegressionEval:
    preds = predictions.ravel()
    lbls = labels.ravel()

    rmse = float(math.sqrt(mean_squared_error(lbls, preds)))
    mae = float(mean_absolute_error(lbls, preds))
    r2 = float(r2_score(lbls, preds))

    residuals = lbls - preds
    res_min, res_max = float(residuals.min()), float(residuals.max())
    width = (res_max - res_min) / RESIDUAL_HISTOGRAM_BINS if res_min != res_max else 1.0
    hist_bins: list[HistogramBin] = []
    for i in range(RESIDUAL_HISTOGRAM_BINS):
        lo = res_min + i * width
        hi = lo + width
        cnt = int(((residuals >= lo) & (residuals < hi)).sum())
        if i == RESIDUAL_HISTOGRAM_BINS - 1:
            cnt = int(((residuals >= lo) & (residuals <= hi)).sum())
        hist_bins.append(HistogramBin(lower=lo, upper=hi, count=cnt))

    # Scatter — downsample for large datasets
    if len(preds) > SCATTER_MAX_POINTS:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(preds), SCATTER_MAX_POINTS, replace=False)
        scatter_p, scatter_l = preds[idx], lbls[idx]
    else:
        scatter_p, scatter_l = preds, lbls

    scatter = [
        ScatterPoint(predicted=float(p), actual=float(a))
        for p, a in zip(scatter_p, scatter_l, strict=False)
    ]

    lo_pct, hi_pct = PREDICTION_INTERVAL_PERCENTILES
    lower_bound = float(np.percentile(residuals, lo_pct))
    upper_bound = float(np.percentile(residuals, hi_pct))
    interval_band = [
        IntervalPoint(
            predicted=float(p),
            lower=float(p) + lower_bound,
            upper=float(p) + upper_bound,
        )
        for p in scatter_p
    ]

    return RegressionEval(
        objective="regression",
        rmse=rmse,
        mae=mae,
        r2=r2,
        residuals_histogram=hist_bins,
        scatter=scatter,
        interval_band=interval_band,
    )


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def _evaluate_ranking(
    predictions: np.ndarray,
    labels: np.ndarray,
    query_ids: np.ndarray,
) -> RankingEval:
    unique_queries = np.unique(query_ids)

    ndcg_at_k: list[NDCGAtK] = []
    for k in NDCG_K_VALUES:
        scores_by_query: list[float] = []
        for qid in unique_queries:
            mask = query_ids == qid
            q_preds = predictions[mask]
            q_labels = labels[mask]
            if len(q_labels) < 2:
                continue
            q_ndcg = ndcg_score(
                q_labels.reshape(1, -1), q_preds.reshape(1, -1), k=min(k, len(q_labels))
            )
            scores_by_query.append(float(q_ndcg))
        val = float(np.mean(scores_by_query)) if scores_by_query else 0.0
        ndcg_at_k.append(NDCGAtK(k=k, value=val))

    # MAP via average_precision_score per query (binary relevance: label > 0)
    ap_scores: list[float] = []
    for qid in unique_queries:
        mask = query_ids == qid
        q_preds = predictions[mask]
        q_labels = (labels[mask] > 0).astype(int)
        if q_labels.sum() == 0 or q_labels.sum() == len(q_labels):
            continue
        ap_scores.append(float(average_precision_score(q_labels, q_preds)))
    mean_ap = float(np.mean(ap_scores)) if ap_scores else 0.0

    per_query_ndcg_at_10: list[float] = []
    for qid in unique_queries:
        mask = query_ids == qid
        q_preds = predictions[mask]
        q_labels = labels[mask]
        if len(q_labels) < 2:
            per_query_ndcg_at_10.append(0.0)
            continue
        k10 = min(10, len(q_labels))
        per_query_ndcg_at_10.append(
            float(ndcg_score(q_labels.reshape(1, -1), q_preds.reshape(1, -1), k=k10))
        )

    return RankingEval(
        objective="lambdarank",
        ndcg_at_k=ndcg_at_k,
        mean_average_precision=mean_ap,
        per_query_ndcg=per_query_ndcg_at_10,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cm_to_cells(cm: Any) -> list[ConfusionCell]:
    cells: list[ConfusionCell] = []
    for actual_idx, row in enumerate(cm):
        for predicted_idx, count in enumerate(row):
            cells.append(
                ConfusionCell(
                    predicted=predicted_idx,
                    actual=actual_idx,
                    count=int(count),
                )
            )
    return cells
