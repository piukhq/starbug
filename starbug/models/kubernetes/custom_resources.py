"""Module containing custom Kubernetes resources."""

from kr8s.objects import APIObject


class SecretProviderClass(APIObject):
    """SecretProviderClass Class."""

    version = "secrets-store.csi.x-k8s.io/v1"
    endpoint = "secretproviderclasses"
    kind = "SecretProviderClass"
    namespaced = True
    singular = True
