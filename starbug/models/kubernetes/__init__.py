"""Kubernetes Models."""

def wait_for_migration(name: str) -> dict:
    """Return a wait-for init container."""
    return {
        "name": "wait-for-migration",
        "image": "ghcr.io/groundnuty/k8s-wait-for:v2.0",
        "imagePullPolicy": "Always",
        "args": ["job", f"{name}-migrator"],
    }
