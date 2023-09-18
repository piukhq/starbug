"""Defines an imagePullSecret for binkcore.azurecr.io Secret."""
from kr8s.objects import Secret


class BinkCore:
    """Defines an imagePullSecret for binkcore.azurecr.io Secret."""

    def __init__(self, namespace: str) -> None:
        """Initialize the Binkcore Class."""
        self.namespace = namespace
        self.secret = Secret({
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "binkcore.azurecr.io",
                "namespace": self.namespace,
            },
            "type": "kubernetes.io/dockerconfigjson",
            "data": {
                ".dockerconfigjson": "eyJhdXRocyI6IHsiYmlua2NvcmUuYXp1cmVjci5pbyI6IHsidXNlcm5hbWUiOiAiYmlua2NvcmUiLCAicGFzc3dvcmQiOiAiaVpJRG05NEU0Uz1pWTZZWWVXSjRKNkk5UXNSbllqaUsiLCAiZW1haWwiOiAiZGV2b3BzQGJpbmsuY29tIiwgImF1dGgiOiAiWW1sdWEyTnZjbVU2YVZwSlJHMDVORVUwVXoxcFdUWlpXV1ZYU2pSS05razVVWE5TYmxscWFVcz0ifX19",  # noqa: E501
            },
        })

    def __iter__(self) -> tuple[Secret]:
        """Iterate over the Kiroshi Instance."""
        yield from (self.secret)
