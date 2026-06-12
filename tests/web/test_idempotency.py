"""Idempotency-Key replay cache (WEB-05)."""

import itertools

from fastapi import FastAPI
from fastapi.testclient import TestClient

from py_launch_blueprint.web.idempotency import IdempotencyMiddleware

counter = itertools.count()


def make_app(**kwargs) -> FastAPI:
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware, **kwargs)

    @app.post("/things")
    def create_thing():
        return {"n": next(counter)}

    @app.post("/fails")
    def always_fails():
        from fastapi import HTTPException

        raise HTTPException(status_code=500)

    return app


def test_same_key_replays_first_response():
    with TestClient(make_app()) as client:
        first = client.post("/things", headers={"Idempotency-Key": "k1"})
        second = client.post("/things", headers={"Idempotency-Key": "k1"})
        assert first.json() == second.json()
        assert "idempotency-replayed" not in first.headers
        assert second.headers["idempotency-replayed"] == "true"


def test_different_keys_execute_independently():
    with TestClient(make_app()) as client:
        a = client.post("/things", headers={"Idempotency-Key": "a"})
        b = client.post("/things", headers={"Idempotency-Key": "b"})
        assert a.json() != b.json()


def test_no_key_means_no_caching():
    with TestClient(make_app()) as client:
        a = client.post("/things")
        b = client.post("/things")
        assert a.json() != b.json()


def test_errors_are_not_cached(monkeypatch):
    with TestClient(make_app(), raise_server_exceptions=False) as client:
        first = client.post("/fails", headers={"Idempotency-Key": "e1"})
        second = client.post("/fails", headers={"Idempotency-Key": "e1"})
        assert first.status_code == second.status_code == 500
        assert "idempotency-replayed" not in second.headers


def test_lru_eviction():
    with TestClient(make_app(max_entries=1)) as client:
        first = client.post("/things", headers={"Idempotency-Key": "k1"})
        client.post("/things", headers={"Idempotency-Key": "k2"})  # evicts k1
        retried = client.post("/things", headers={"Idempotency-Key": "k1"})
        assert retried.json() != first.json()
        assert "idempotency-replayed" not in retried.headers
