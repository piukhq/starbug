"""Module containing custom Kubernetes resources."""

from kr8s.objects import APIObject


class StarbugTest(APIObject):
    """StarbugTest Class."""

    version = "bink.com/v1beta1"
    endpoint = "tests"
    kind = "StarbugTest"
    plural = "tests"
    singular = "test"
    namespaced = True
    scalable = False
