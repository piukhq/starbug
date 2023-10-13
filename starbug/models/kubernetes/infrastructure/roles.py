"""Defines any Roles needed for the namespace."""

from kr8s.objects import Role


class Roles:
    """Defines any Roles needed for the namespace."""

    def __init__(self, namespace: str | None = None) -> None:
        """Initialize the Roles class."""
        self.namespace = namespace or "default"
        self.k8s_wait_for = Role({
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {
                "name": "k8s-wait-for",
                "namespace": self.namespace,
            },
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": ["pods", "services"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["apps"],
                    "resources": ["deployments"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["batch"],
                    "resources": ["jobs"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
        })

    def complete(self) -> tuple[Role]:
        """Return all deployable objects as a tuple."""
        return (self.k8s_wait_for, )
