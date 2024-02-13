"""Defines a Namespace."""

import json

from kr8s.objects import Namespace as Ns


class Namespace:
    """Defines a Namespace."""

    def __init__(self, name: str) -> None:
        """Initialize the Namespace Class."""
        self.name: str = name
        self.linkerd_inject: str = "enabled"
        self.tolerations: list = [
            {"key": "bink.com/workload", "operator": "Equal", "value": "txm", "effect": "NoSchedule"},
            {
                "key": "kubernetes.azure.com/scalesetpriority",
                "operator": "Equal",
                "value": "spot",
                "effect": "NoSchedule",
            },
        ]
        self.node_selector: str = "kubernetes.azure.com/scalesetpriority=spot"

        self.namespace = Ns(
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "annotations": {
                        "linkerd.io/inject": self.linkerd_inject,
                        "scheduler.alpha.kubernetes.io/defaultTolerations": json.dumps(self.tolerations),
                        "scheduler.alpha.kubernetes.io/node-selector": self.node_selector,
                    },
                    "name": self.name,
                },
            },
        )

    def deploy(self) -> tuple[Ns]:
        """Return all deployable objects as a tuple."""
        return (self.namespace,)
