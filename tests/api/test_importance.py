"""Tests for GET /artifacts/{id}/importance."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_gain_returns_sorted_features(
    client: TestClient, written_artifact_id: str
) -> None:
    resp = client.get(f"/artifacts/{written_artifact_id}/importance?type=gain")
    assert resp.status_code == 200
    body = resp.json()
    assert body["artifact_id"] == written_artifact_id
    assert body["type"] == "gain"
    assert len(body["features"]) == 2
    values = [f["value"] for f in body["features"]]
    assert values == sorted(values, reverse=True)


def test_split_returns_sorted_features(
    client: TestClient, written_artifact_id: str
) -> None:
    resp = client.get(f"/artifacts/{written_artifact_id}/importance?type=split")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "split"
    assert len(body["features"]) == 2


def test_permutation_no_data_returns_200_empty(
    client: TestClient, written_artifact_id: str
) -> None:
    """When permutation was not computed, endpoint returns 200 with empty features."""
    resp = client.get(f"/artifacts/{written_artifact_id}/importance?type=permutation")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "permutation"
    assert body["features"] == []
    assert "detail" in body
    assert "not computed" in body["detail"]


def test_invalid_type_returns_422(client: TestClient, written_artifact_id: str) -> None:
    resp = client.get(f"/artifacts/{written_artifact_id}/importance?type=gini")
    assert resp.status_code == 422


def test_missing_type_param_returns_422(
    client: TestClient, written_artifact_id: str
) -> None:
    resp = client.get(f"/artifacts/{written_artifact_id}/importance")
    assert resp.status_code == 422


def test_unknown_artifact_returns_404(client: TestClient) -> None:
    resp = client.get("/artifacts/no_such_artifact/importance?type=gain")
    assert resp.status_code == 404


def test_gain_features_have_rank_gain(
    client: TestClient, written_artifact_id: str
) -> None:
    resp = client.get(f"/artifacts/{written_artifact_id}/importance?type=gain")
    body = resp.json()
    for feature in body["features"]:
        assert "rank_gain" in feature
        assert isinstance(feature["rank_gain"], int)
        assert feature["rank_gain"] >= 1
