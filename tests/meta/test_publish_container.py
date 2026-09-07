"""Behavioral guards for release replay, publication identity, and promotion."""

import hashlib
import importlib.util
import io
import json
import sys
from http.client import HTTPMessage
from pathlib import Path
from unittest.mock import Mock
from urllib.error import HTTPError
from urllib.request import Request

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "publish_container", ROOT / "scripts/publish_container.py"
)
pub = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pub
SPEC.loader.exec_module(pub)

REPOSITORY = "example-org/service"
REVISION = "a" * 40
IMAGE_ID = "sha256:" + "b" * 64
CONFIG_DIGEST = "sha256:" + "e" * 64


def image(version="2.10.0", revision=REVISION, config=CONFIG_DIGEST):
    raw = json.dumps(
        {"mediaType": pub.MEDIA_TYPES[0], "config": {"digest": config}}
    ).encode()
    manifest = pub.Manifest(
        raw, "sha256:" + hashlib.sha256(raw).hexdigest(), config, pub.MEDIA_TYPES[0]
    )
    labels = {
        "org.opencontainers.image.source": f"https://github.com/{REPOSITORY}",
        "org.opencontainers.image.version": version,
        "org.opencontainers.image.revision": revision,
    }
    return manifest, labels


@pytest.fixture
def effects(monkeypatch):
    mocks = {}
    for name in ("build", "run", "pull_test", "verify_public"):
        mocks[name] = Mock(
            return_value=pub.BuiltImage(IMAGE_ID, CONFIG_DIGEST)
            if name == "build"
            else None
        )
        monkeypatch.setattr(pub, name, mocks[name])
    return mocks


def test_first_publish_pushes_the_tested_id(effects):
    manifest, labels = image()
    registry = Mock(spec=pub.Registry)
    registry.manifest.side_effect = [None, manifest]
    registry.labels.return_value = labels

    assert pub.publish(REPOSITORY, "2.10.0", REVISION, registry, {}) == manifest

    effects["build"].assert_called_once_with(REPOSITORY, "2.10.0", REVISION)
    assert effects["run"].call_args_list[0].args == (
        "docker",
        "tag",
        IMAGE_ID,
        f"ghcr.io/{REPOSITORY}:2.10.0",
    )
    assert effects["run"].call_args_list[1].args == (
        "docker",
        "push",
        "--platform=linux/amd64",
        f"ghcr.io/{REPOSITORY}:2.10.0",
    )
    effects["verify_public"].assert_called_once_with(REPOSITORY, manifest)


@pytest.mark.parametrize("docker_id", [IMAGE_ID, CONFIG_DIGEST])
def test_build_binds_config_digest_independently_of_docker_storage_backend(
    monkeypatch, docker_id
):
    def commands(*args):
        if args[1] == "buildx":
            metadata = Path(args[args.index("--metadata-file") + 1])
            metadata.write_text(
                json.dumps({"containerimage.config.digest": CONFIG_DIGEST})
            )
            return ""
        return docker_id

    monkeypatch.setattr(pub, "run", commands)
    smoke = Mock()
    monkeypatch.setattr(pub, "smoke_test", smoke)
    assert pub.build(REPOSITORY, "2.10.0", REVISION) == pub.BuiltImage(
        docker_id, CONFIG_DIGEST
    )
    smoke.assert_called_once_with(docker_id, "2.10.0")


def test_digest_pull_resolves_the_daemons_runnable_id(monkeypatch):
    manifest, _ = image()
    commands = Mock(side_effect=["", IMAGE_ID])
    monkeypatch.setattr(pub, "run", commands)
    smoke = Mock()
    monkeypatch.setattr(pub, "smoke_test", smoke)
    pub.pull_test(REPOSITORY, "2.10.0", manifest, {})
    assert commands.call_args.args[-1] == f"ghcr.io/{REPOSITORY}@{manifest.digest}"
    smoke.assert_called_once_with(IMAGE_ID, "2.10.0")


def test_rerun_reuses_existing_digest_without_building_or_pushing(effects):
    manifest, labels = image()
    registry = Mock(spec=pub.Registry)
    registry.manifest.return_value = manifest
    registry.labels.return_value = labels

    pub.publish(REPOSITORY, "2.10.0", REVISION, registry, {})

    effects["build"].assert_not_called()
    effects["run"].assert_not_called()
    effects["pull_test"].assert_called_once_with(REPOSITORY, "2.10.0", manifest, {})


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("org.opencontainers.image.revision", "c" * 40),
        ("org.opencontainers.image.source", "https://github.com/somewhere/else"),
        ("org.opencontainers.image.version", "2.9.0"),
    ],
)
def test_conflicting_existing_version_stops_before_any_write(effects, key, value):
    manifest, labels = image()
    labels[key] = value
    registry = Mock(spec=pub.Registry)
    registry.manifest.return_value = manifest
    registry.labels.return_value = labels

    with pytest.raises(ValueError, match="conflicts"):
        pub.publish(REPOSITORY, "2.10.0", REVISION, registry, {})
    for effect in effects.values():
        effect.assert_not_called()


def test_registry_failure_does_not_authorize_a_build(effects):
    registry = Mock(spec=pub.Registry)
    registry.manifest.side_effect = HTTPError(
        "https://ghcr.io", 401, "denied", {}, None
    )
    with pytest.raises(HTTPError):
        pub.publish(REPOSITORY, "2.10.0", REVISION, registry, {})
    effects["build"].assert_not_called()
    effects["run"].assert_not_called()


def test_push_with_different_config_is_not_accepted(effects):
    manifest, _ = image(config="sha256:" + "d" * 64)
    registry = Mock(spec=pub.Registry)
    registry.manifest.side_effect = [None, manifest]
    with pytest.raises(ValueError, match="exact smoke-tested image"):
        pub.publish(REPOSITORY, "2.10.0", REVISION, registry, {})
    effects["verify_public"].assert_not_called()


@pytest.mark.parametrize(
    ("status", "code", "missing"),
    [
        (404, "MANIFEST_UNKNOWN", True),
        (404, "NAME_UNKNOWN", True),
        (404, "UNAUTHORIZED", False),
        (403, "DENIED", False),
        (401, "UNAUTHORIZED", False),
        (500, "MANIFEST_UNKNOWN", False),
    ],
)
def test_only_explicit_missing_manifest_responses_allow_publication(
    status, code, missing
):
    registry = object.__new__(pub.Registry)
    registry.repository = REPOSITORY
    body = io.BytesIO(json.dumps({"errors": [{"code": code}]}).encode())
    registry.request = Mock(
        side_effect=HTTPError("https://ghcr.io", status, code, {}, body)
    )
    if missing:
        assert registry.manifest("2.10.0") is None
    else:
        with pytest.raises(HTTPError):
            registry.manifest("2.10.0")


def test_manifest_digest_is_verified_against_received_bytes():
    manifest, _ = image()
    registry = object.__new__(pub.Registry)
    registry.repository = REPOSITORY
    registry.request = Mock(
        return_value=(manifest.raw, {"docker-content-digest": manifest.digest})
    )
    assert registry.manifest("2.10.0") == manifest
    registry.request.return_value = (manifest.raw, {"docker-content-digest": IMAGE_ID})
    with pytest.raises(ValueError, match="digest does not match"):
        registry.manifest("2.10.0")


def test_existing_index_is_detected_and_refused_not_mistaken_for_absence(monkeypatch):
    raw = json.dumps({"mediaType": pub.INDEX_MEDIA_TYPES[0], "manifests": []}).encode()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()

    def server(request, timeout):
        # Reproduce GHCR's real content negotiation: an unaccepted index looks
        # missing even though the version tag is occupied.
        if pub.INDEX_MEDIA_TYPES[0] not in request.get_header("Accept"):
            body = io.BytesIO(
                json.dumps({"errors": [{"code": "MANIFEST_UNKNOWN"}]}).encode()
            )
            raise HTTPError(request.full_url, 404, "Not Found", {}, body)
        response = io.BytesIO(raw)
        response.headers = {"Docker-Content-Digest": digest}
        return response

    monkeypatch.setattr(pub.OPENER, "open", server)
    registry = object.__new__(pub.Registry)
    registry.repository = REPOSITORY
    registry.headers = {}
    with pytest.raises(ValueError, match="single-platform"):
        registry.manifest("2.10.0")


def test_versions_are_numeric_stable_and_paginated():
    registry = object.__new__(pub.Registry)
    registry.repository = REPOSITORY
    registry.request = Mock(
        side_effect=[
            (
                json.dumps(
                    {"tags": ["2.9.0", "2.10.0-rc.1", "latest", "02.0.0"]}
                ).encode(),
                {"link": f'</v2/{REPOSITORY}/tags/list?last=2.9.0>; rel="next"'},
            ),
            (json.dumps({"tags": ["2.10.0", "1.0.0"]}).encode(), {}),
        ]
    )
    assert registry.versions() == ["1.0.0", "2.9.0", "2.10.0"]


def test_registry_pagination_cannot_send_credentials_to_another_host():
    registry = object.__new__(pub.Registry)
    registry.repository = REPOSITORY
    with pytest.raises(ValueError, match=r"leave ghcr\.io"):
        registry.request("https://example.com/steal")


def test_blob_redirect_strips_registry_credentials():
    request = Request(
        "https://ghcr.io/v2/example-org/service/blobs/sha256:abc",
        headers={"Authorization": "Bearer test-only"},
    )
    redirected = pub.RegistryRedirects().redirect_request(
        request,
        io.BytesIO(),
        307,
        "Redirect",
        HTTPMessage(),
        "https://pkg-containers.githubusercontent.com/signed-blob",
    )
    assert redirected.get_header("Authorization") is None
    with pytest.raises(ValueError, match="requires HTTPS"):
        pub.RegistryRedirects().redirect_request(
            request,
            io.BytesIO(),
            307,
            "Redirect",
            HTTPMessage(),
            "http://example.com/insecure-blob",
        )


def test_old_promotion_selects_the_highest_published_version(effects):
    newest, labels = image("2.10.0")
    registry = Mock(spec=pub.Registry)
    registry.versions.return_value = ["2.9.0", "2.10.0"]
    registry.manifest.side_effect = [newest, None]
    registry.labels.return_value = labels

    # The helper intentionally takes no triggering version. A surviving old
    # job must also cover a newer promotion that GitHub replaced while pending.
    assert pub.promote_latest(REPOSITORY, registry, {}) == newest
    registry.manifest.assert_any_call("2.10.0")
    registry.promote.assert_called_once_with(newest)
    effects["pull_test"].assert_called_once_with(REPOSITORY, "2.10.0", newest, {})
    effects["build"].assert_not_called()


@pytest.mark.parametrize("current_version", ["3.0.0", "2.10.0"])
def test_latest_does_not_regress_or_replace_conflicting_bytes(effects, current_version):
    candidate, candidate_labels = image()
    current, current_labels = image(current_version, config="sha256:" + "c" * 64)
    registry = Mock(spec=pub.Registry)
    registry.versions.return_value = ["2.10.0"]
    registry.manifest.side_effect = [candidate, current]
    registry.labels.side_effect = [candidate_labels, current_labels]

    with pytest.raises(ValueError, match=r"backward|conflicts"):
        pub.promote_latest(REPOSITORY, registry, {})
    registry.promote.assert_not_called()


def test_promotion_copies_manifest_bytes_without_wrapping_in_an_index():
    manifest, _ = image()
    registry = object.__new__(pub.Registry)
    registry.repository = REPOSITORY
    registry.request = Mock()
    registry.manifest = Mock(return_value=manifest)
    registry.promote(manifest)
    registry.request.assert_called_once_with(
        f"/v2/{REPOSITORY}/manifests/latest",
        data=manifest.raw,
        media_type=manifest.media_type,
    )


def test_public_check_uses_an_empty_temporary_docker_configuration(monkeypatch):
    manifest, _ = image()
    directories = []

    def pull(*args, env):
        directory = Path(env["DOCKER_CONFIG"])
        directories.append(directory)
        assert directory.is_dir()
        assert list(directory.iterdir()) == []
        assert args == (
            "docker",
            "pull",
            "--platform=linux/amd64",
            f"ghcr.io/{REPOSITORY}@{manifest.digest}",
        )

    monkeypatch.setattr(pub, "run", pull)
    pub.verify_public(REPOSITORY, manifest)
    assert len(directories) == 1
    assert not directories[0].exists()


@pytest.fixture
def release_event(monkeypatch, tmp_path):
    event = {
        "action": "published",
        "release": {"draft": False, "prerelease": False, "tag_name": "v2.10.0"},
    }
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "release")
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v2.10.0")
    monkeypatch.setenv("GITHUB_SHA", REVISION)
    monkeypatch.setattr(pub, "run", Mock(return_value=REVISION))
    return event, path


def test_release_validation_checks_tag_commit_and_main_ancestry(release_event):
    assert pub.release_revision("2.10.0") == REVISION
    pub.run.assert_any_call("git", "rev-parse", "refs/tags/v2.10.0^{commit}")
    pub.run.assert_any_call(
        "git", "merge-base", "--is-ancestor", REVISION, "refs/remotes/origin/main"
    )


@pytest.mark.parametrize(
    ("field", "value"), [("draft", True), ("prerelease", True), ("tag_name", "v2.9.0")]
)
def test_invalid_release_metadata_is_refused(release_event, field, value):
    event, path = release_event
    event["release"][field] = value
    path.write_text(json.dumps(event))
    with pytest.raises(ValueError, match="matching published stable"):
        pub.release_revision("2.10.0")
    pub.run.assert_not_called()


def test_moved_tag_is_refused(release_event):
    pub.run.side_effect = [REVISION, "d" * 40]
    with pytest.raises(ValueError, match="disagree"):
        pub.release_revision("2.10.0")


def test_pr_cannot_enter_publishing_even_if_workflow_gate_is_removed(
    release_event, monkeypatch
):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REPOSITORY", REPOSITORY)
    monkeypatch.setattr(pub, "source_version", lambda: "2.10.0")
    registry = Mock()
    monkeypatch.setattr(pub, "Registry", registry)
    monkeypatch.setattr(sys, "argv", ["publish_container.py", "publish"])
    with pytest.raises(ValueError, match="matching published stable"):
        pub.main()
    registry.assert_not_called()
