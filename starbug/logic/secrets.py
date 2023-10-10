"""Helper fuctions for Kubernetes Secrets."""

from base64 import b64decode

from kr8s.objects import Secret


def get_secret_value(name: str, key: str, namespace: str = "default") -> str:
    """Get the Value of a Secret."""
    secret = Secret.get(name=name, namespace=namespace)
    return b64decode(secret.raw["data"][key]).decode("utf-8")
