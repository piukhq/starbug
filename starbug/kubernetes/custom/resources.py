"""Module containing custom Kubernetes resources."""

from kr8s.objects import APIObject


class SecretProviderClass(APIObject):
    """SecretProviderClass Class."""

    version = "secrets-store.csi.x-k8s.io/v1"
    endpoint = "secretproviderclasses"
    kind = "SecretProviderClass"
    plural = "secretproviderclasses"
    singular = "secretproviderclass"
    namespaced = True
    scalable = False


class StarbugTest(APIObject):
    """StarbugTest Class."""

    version = "bink.com/v1"
    endpoint = "tests"
    kind = "StarbugTest"
    plural = "tests"
    singular = "test"
    namespaced = True
    scalable = False
