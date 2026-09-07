"""Build, verify, and publish the web image without rebuilding released versions.

The workflow supplies GitHub's short-lived token. Registry errors fail closed;
only an explicit missing-manifest response permits a new version to be built.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import tomllib
from dataclasses import dataclass
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, override
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
STABLE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}")
MEDIA_TYPES = (
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
)
INDEX_MEDIA_TYPES = (
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
)


class RegistryRedirects(HTTPRedirectHandler):
    """Signed blob redirects must not receive the registry's bearer token."""

    @override
    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> Request | None:
        if urlsplit(newurl).scheme != "https":
            raise ValueError("Registry redirect requires HTTPS")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header("Authorization")
            redirected.remove_header("Proxy-authorization")
        return redirected


OPENER = build_opener(RegistryRedirects())


def version_number(value: str) -> tuple[int, int, int]:
    match = STABLE.fullmatch(value)
    if not match:
        raise ValueError(f"Expected a stable X.Y.Z version, got {value!r}")
    return int(match[1]), int(match[2]), int(match[3])


def run(
    *args: str, env: dict[str, str] | None = None, input_text: str | None = None
) -> str:
    executable = shutil.which(args[0])
    if executable is None:
        raise RuntimeError(f"Required executable is missing: {args[0]}")
    result = subprocess.run(  # noqa: S603 -- argument vector, never a shell
        [executable, *args[1:]],
        cwd=ROOT,
        env=env,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{args[0]} {args[1]} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


@dataclass(frozen=True)
class Manifest:
    raw: bytes
    digest: str
    config: str
    media_type: str


@dataclass(frozen=True)
class BuiltImage:
    image_id: str
    config_digest: str


class Registry:
    """The small authenticated subset of the OCI distribution API used here."""

    def __init__(self, repository: str) -> None:
        self.repository = repository
        query = urlencode(
            {"service": "ghcr.io", "scope": f"repository:{repository}:pull,push"}
        )
        credentials = f"{os.environ['GITHUB_ACTOR']}:{os.environ['GHCR_TOKEN']}"
        basic = base64.b64encode(credentials.encode()).decode()
        request = Request(
            f"https://ghcr.io/token?{query}",
            headers={"Authorization": f"Basic {basic}"},
        )
        with OPENER.open(request, timeout=30) as response:
            token = json.load(response)["token"]
        if not isinstance(token, str) or not token:
            raise ValueError("Registry did not return an authentication token")
        self.headers = {"Authorization": f"Bearer {token}"}

    def request(
        self, path: str, *, data: bytes | None = None, media_type: str | None = None
    ) -> tuple[bytes, dict[str, str]]:
        url = urljoin("https://ghcr.io", path)
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.netloc != "ghcr.io":
            raise ValueError("Registry pagination attempted to leave ghcr.io")
        if (
            parts.path != f"/v2/{self.repository}/tags/list"
            and not parts.path.startswith(
                (f"/v2/{self.repository}/manifests/", f"/v2/{self.repository}/blobs/")
            )
        ):
            raise ValueError("Unexpected registry path")
        # GHCR reports MANIFEST_UNKNOWN when an existing index is not accepted.
        # Request indexes too, then refuse them explicitly in manifest().
        headers = {
            **self.headers,
            "Accept": ", ".join((*MEDIA_TYPES, *INDEX_MEDIA_TYPES)),
        }
        if media_type:
            headers["Content-Type"] = media_type
        request = Request(  # noqa: S310 -- validated HTTPS host and repository path
            url, data=data, headers=headers, method="PUT" if data else "GET"
        )
        with OPENER.open(request, timeout=30) as response:
            return response.read(), {
                key.lower(): value for key, value in response.headers.items()
            }

    def manifest(self, tag: str) -> Manifest | None:
        try:
            raw, headers = self.request(f"/v2/{self.repository}/manifests/{tag}")
        except HTTPError as error:
            if error.code != 404:
                raise
            body = json.load(error)
            codes = {entry.get("code") for entry in body.get("errors", [])}
            if not codes or not codes <= {"MANIFEST_UNKNOWN", "NAME_UNKNOWN"}:
                raise
            return None
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        if headers.get("docker-content-digest") != digest:
            raise ValueError("Registry manifest digest does not match its bytes")
        document = json.loads(raw)
        media_type = document.get("mediaType")
        if media_type not in MEDIA_TYPES:
            raise ValueError("Expected a single-platform image manifest")
        config = document["config"]["digest"]
        if not DIGEST.fullmatch(config):
            raise ValueError("Invalid image configuration digest")
        return Manifest(raw, digest, config, media_type)

    def labels(self, manifest: Manifest) -> dict[str, str]:
        raw, _ = self.request(f"/v2/{self.repository}/blobs/{manifest.config}")
        if "sha256:" + hashlib.sha256(raw).hexdigest() != manifest.config:
            raise ValueError("Image configuration digest does not match its bytes")
        config = json.loads(raw)
        if not isinstance(config, dict) or (
            config.get("os"),
            config.get("architecture"),
        ) != ("linux", "amd64"):
            raise ValueError("Expected a linux/amd64 image")
        image_config = config.get("config")
        labels = image_config.get("Labels") if isinstance(image_config, dict) else None
        if not isinstance(labels, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in labels.items()
        ):
            raise ValueError("Expected string image labels")
        return labels

    def versions(self) -> list[str]:
        path = f"/v2/{self.repository}/tags/list?n=1000"
        seen: set[str] = set()
        versions: set[str] = set()
        while path:
            if path in seen:
                raise ValueError("Registry pagination repeated a page")
            seen.add(path)
            raw, headers = self.request(path)
            for tag in json.loads(raw).get("tags") or []:
                if STABLE.fullmatch(tag):
                    versions.add(tag)
            link = headers.get("link", "")
            if link:
                match = re.fullmatch(r'<([^>]+)>;\s*rel="next"', link)
                if not match:
                    raise ValueError("Unexpected registry pagination link")
                path = match[1]
            else:
                path = ""
        return sorted(versions, key=version_number)

    def promote(self, manifest: Manifest) -> None:
        self.request(
            f"/v2/{self.repository}/manifests/latest",
            data=manifest.raw,
            media_type=manifest.media_type,
        )
        actual = self.manifest("latest")
        if actual is None or actual.digest != manifest.digest:
            raise ValueError("latest did not retain the version's manifest digest")


def repository_name() -> str:
    repository = os.environ["GITHUB_REPOSITORY"].lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9._-]*", repository):
        raise ValueError("Invalid GitHub owner/repository")
    return repository


def source_version() -> str:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    version = project["project"]["version"]
    version_number(version)
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    root_versions = [
        package["version"]
        for package in lock["package"]
        if package.get("source", {}).get("editable") == "."
    ]
    if root_versions != [version]:
        raise ValueError("uv.lock editable root version does not match pyproject.toml")
    return version


def release_revision(version: str) -> str:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    release = event["release"]
    tag = f"v{version}"
    if (
        os.environ["GITHUB_EVENT_NAME"] != "release"
        or event["action"] != "published"
        or release["draft"] is not False
        or release["prerelease"] is not False
        or release["tag_name"] != tag
        or os.environ["GITHUB_REF"] != f"refs/tags/{tag}"
    ):
        raise ValueError("Publishing requires a matching published stable release")
    revision = run("git", "rev-parse", "HEAD")
    if (
        revision != os.environ["GITHUB_SHA"]
        or run("git", "rev-parse", f"refs/tags/{tag}^{{commit}}") != revision
    ):
        raise ValueError("Release tag, event commit, and checkout disagree")
    run("git", "merge-base", "--is-ancestor", revision, "refs/remotes/origin/main")
    return revision


def verify_labels(
    labels: dict[str, str], repository: str, version: str, revision: str | None = None
) -> None:
    actual_revision = labels.get("org.opencontainers.image.revision", "")
    if (
        labels.get("org.opencontainers.image.source")
        != f"https://github.com/{repository}"
        or labels.get("org.opencontainers.image.version") != version
        or not REVISION.fullmatch(actual_revision)
        or (revision is not None and actual_revision != revision)
    ):
        raise ValueError("Existing image source, version, or revision conflicts")


def smoke_test(image_id: str, version: str) -> None:
    if not DIGEST.fullmatch(image_id):
        raise ValueError("Smoke tests must run an exact local image ID")
    container = run(
        "docker", "run", "--platform=linux/amd64", "--detach", "--pull=never", image_id
    )
    probe = (
        "import json, os, urllib.request; "
        "health=json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)); "
        "print(json.dumps({'health': health, 'uid': os.geteuid()}))"
    )
    try:
        deadline = time.monotonic() + 90
        while True:
            try:
                result = json.loads(
                    run("docker", "exec", container, "python", "-c", probe)
                )
                break
            except RuntimeError:
                if (
                    time.monotonic() >= deadline
                    or run(
                        "docker", "inspect", "--format", "{{.State.Running}}", container
                    )
                    != "true"
                ):
                    raise
                time.sleep(1)
        if (
            result["health"].get("status") != "ok"
            or result["health"].get("version") != version
        ):
            raise ValueError("Container health response does not match the release")
        if result["uid"] == 0:
            raise ValueError("Container runs as root")
        print(
            f"Smoke test passed: version {version}, uid {result['uid']}, {image_id}",
            flush=True,
        )
    finally:
        run("docker", "rm", "--force", container)


def build(repository: str, version: str, revision: str) -> BuiltImage:
    image = f"ghcr.io/{repository}:{version}"
    print(f"Building and testing {image}", flush=True)
    with tempfile.TemporaryDirectory(prefix="ghcr-build-") as directory:
        metadata = Path(directory) / "metadata.json"
        run(
            "docker",
            "buildx",
            "build",
            "--load",
            "--platform",
            "linux/amd64",
            "--provenance=false",
            "--metadata-file",
            str(metadata),
            "--label",
            f"org.opencontainers.image.source=https://github.com/{repository}",
            "--label",
            f"org.opencontainers.image.version={version}",
            "--label",
            f"org.opencontainers.image.revision={revision}",
            "--tag",
            image,
            ".",
        )
        config_digest = json.loads(metadata.read_text())["containerimage.config.digest"]
        if not DIGEST.fullmatch(config_digest):
            raise ValueError("Buildx did not record a valid configuration digest")
    image_id = run("docker", "image", "inspect", "--format", "{{.Id}}", image)
    smoke_test(image_id, version)
    return BuiltImage(image_id, config_digest)


def pull_test(
    repository: str, version: str, manifest: Manifest, env: dict[str, str]
) -> None:
    reference = f"ghcr.io/{repository}@{manifest.digest}"
    run(
        "docker",
        "pull",
        "--platform=linux/amd64",
        reference,
        env=env,
    )
    # Docker's classic store uses a config ID; containerd uses a manifest ID.
    # Resolve the runnable ID from the immutable reference on either backend.
    image_id = run(
        "docker", "image", "inspect", "--format", "{{.Id}}", reference, env=env
    )
    smoke_test(image_id, version)


def verify_public(repository: str, manifest: Manifest) -> None:
    with tempfile.TemporaryDirectory(prefix="ghcr-anonymous-") as directory:
        env = {**os.environ, "DOCKER_CONFIG": directory}
        try:
            run(
                "docker",
                "pull",
                "--platform=linux/amd64",
                f"ghcr.io/{repository}@{manifest.digest}",
                env=env,
            )
        except RuntimeError as error:
            raise RuntimeError(
                "Anonymous pull failed. The image may still be private. Set the GHCR "
                "package visibility to Public, then rerun this release; it will reuse "
                "the published image. If already public, check the registry error."
            ) from error


def publish(
    repository: str,
    version: str,
    revision: str,
    registry: Registry,
    env: dict[str, str],
) -> Manifest:
    manifest = registry.manifest(version)
    if manifest is not None:
        verify_labels(registry.labels(manifest), repository, version, revision)
        print(f"Reusing ghcr.io/{repository}@{manifest.digest}", flush=True)
        pull_test(repository, version, manifest, env)
    else:
        built = build(repository, version, revision)
        image = f"ghcr.io/{repository}:{version}"
        run("docker", "tag", built.image_id, image)
        run("docker", "push", "--platform=linux/amd64", image, env=env)
        manifest = registry.manifest(version)
        if manifest is None or manifest.config != built.config_digest:
            raise ValueError("Published image is not the exact smoke-tested image")
        verify_labels(registry.labels(manifest), repository, version, revision)
    verify_public(repository, manifest)
    return manifest


def promote_latest(
    repository: str, registry: Registry, env: dict[str, str]
) -> Manifest:
    versions = registry.versions()
    if not versions:
        raise ValueError("No published stable container version exists")
    version = versions[-1]
    candidate = registry.manifest(version)
    if candidate is None:
        raise ValueError("Newest version disappeared during promotion")
    verify_labels(registry.labels(candidate), repository, version)
    current = registry.manifest("latest")
    if current is not None:
        labels = registry.labels(current)
        current_version = labels.get("org.opencontainers.image.version", "")
        verify_labels(labels, repository, current_version)
        if version_number(current_version) > version_number(version):
            raise ValueError(
                "Refusing to move latest backward; a version tag may have been deleted"
            )
        if current_version == version and current.digest != candidate.digest:
            raise ValueError("Existing latest conflicts with the same version tag")
    # A different release's promotion may have been replaced while pending.
    # Reconcile the highest registry version, regardless of this run's trigger.
    pull_test(repository, version, candidate, env)
    verify_public(repository, candidate)
    registry.promote(candidate)
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("check", "publish", "promote"))
    operation = parser.parse_args().operation
    repository = repository_name()
    if operation == "check":
        build(repository, source_version(), run("git", "rev-parse", "HEAD"))
        return
    version = source_version()
    revision = release_revision(version)
    registry = Registry(repository)
    with tempfile.TemporaryDirectory(prefix="ghcr-publisher-") as directory:
        env = {**os.environ, "DOCKER_CONFIG": directory}
        run(
            "docker",
            "login",
            "ghcr.io",
            "--username",
            os.environ["GITHUB_ACTOR"],
            "--password-stdin",
            env=env,
            input_text=os.environ["GHCR_TOKEN"],
        )
        manifest = (
            publish(repository, version, revision, registry, env)
            if operation == "publish"
            else promote_latest(repository, registry, env)
        )
    reference = f"ghcr.io/{repository}@{manifest.digest}"
    print(f"Verified public image: {reference}")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a") as stream:
            stream.write(f"Public container ({operation}): `{reference}`\n")


if __name__ == "__main__":
    main()
