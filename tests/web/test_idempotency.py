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


def test_errors_are_not_cached():
    with TestClient(make_app(), raise_server_exceptions=False) as client:
        first = client.post("/fails", headers={"Idempotency-Key": "e1"})
        second = client.post("/fails", headers={"Idempotency-Key": "e1"})
        assert first.status_code == second.status_code == 500
        assert "idempotency-replayed" not in second.headers


def test_background_tasks_survive_rebuild():
    ran = []
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post("/with-background")
    def with_background():
        from fastapi import Response
        from starlette.background import BackgroundTask

        return Response(
            content=b"ok", background=BackgroundTask(lambda: ran.append(True))
        )

    with TestClient(app) as client:
        client.post("/with-background", headers={"Idempotency-Key": "bg"})
        assert ran == [True]


def test_same_key_different_query_strings_execute_independently():
    """The cache key includes the query string — no cross-query replays."""
    with TestClient(make_app()) as client:
        a = client.post("/things?a=1", headers={"Idempotency-Key": "q"})
        b = client.post("/things?a=2", headers={"Idempotency-Key": "q"})
        assert a.json() != b.json()
        assert "idempotency-replayed" not in b.headers


def test_multi_valued_headers_survive_caching_and_replay():
    """Set-Cookie must not collapse to one value on rebuild or replay."""
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post("/cookies")
    def set_cookies():
        from fastapi import Response

        response = Response(content=b"ok")
        response.set_cookie("a", "1")
        response.set_cookie("b", "2")
        return response

    with TestClient(app) as client:
        first = client.post("/cookies", headers={"Idempotency-Key": "ck"})
        replay = client.post("/cookies", headers={"Idempotency-Key": "ck"})
        third = client.post("/cookies", headers={"Idempotency-Key": "ck"})
        assert len(first.headers.get_list("set-cookie")) == 2
        assert replay.headers.get_list("set-cookie") == first.headers.get_list(
            "set-cookie"
        )
        assert replay.headers["idempotency-replayed"] == "true"
        # The replay marker must not accumulate in the cached entry.
        assert third.headers.get_list("idempotency-replayed") == ["true"]


def test_lru_eviction():
    with TestClient(make_app(max_entries=1)) as client:
        first = client.post("/things", headers={"Idempotency-Key": "k1"})
        client.post("/things", headers={"Idempotency-Key": "k2"})  # evicts k1
        retried = client.post("/things", headers={"Idempotency-Key": "k1"})
        assert retried.json() != first.json()
        assert "idempotency-replayed" not in retried.headers
