"""Kubernetes Models."""

from base64 import b64decode

from kr8s.objects import Secret


def wait_for_migration(name: str) -> dict:
    """Return a wait-for init container."""
    return {
        "name": "wait-for-migration",
        "image": "ghcr.io/groundnuty/k8s-wait-for:v2.0",
        "imagePullPolicy": "Always",
        "args": ["job-wr", f"{name}-migrator"],
    }


def wait_for_pod(name: str) -> dict:
    """Return a wait-for init container."""
    return {
        "name": f"wait-for-{name}",
        "image": "ghcr.io/groundnuty/k8s-wait-for:v2.0",
        "imagePullPolicy": "Always",
        "args": ["pod", f"-lapp={name}"],
    }


def get_secret_value(name: str, key: str, namespace: str = "default") -> str:
    """Get the Value of a Secret."""
    secret = Secret.get(name=name, namespace=namespace)
    return b64decode(secret.raw["data"][key]).decode("utf-8")
