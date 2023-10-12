"""Defines a Namespace."""

from kr8s.objects import Namespace as Ns


class Namespace:
    """Defines a Namespace."""

    def __init__(self, name: str) -> None:
        """Initialize the Namespace Class."""
        self.name = name

        self.namespace = Ns({
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "annotations": {
                    "linkerd.io/inject": "enabled",
                },
                "name": self.name,
            },
        })

    def complete(self) -> tuple[Ns]:
        """Return all deployable objects as a tuple."""
        return (self.namespace, )
