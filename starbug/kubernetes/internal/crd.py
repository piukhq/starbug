"""Module containing the Custom Resource Definition for Starbug."""

from kr8s.objects import CustomResourceDefinition


def _starbug_crd() -> CustomResourceDefinition:
    return CustomResourceDefinition(
        {
            "apiVersion": "apiextensions.k8s.io/v1",
            "kind": "CustomResourceDefinition",
            "metadata": {"name": "tests.bink.com"},
            "spec": {
                "scope": "Namespaced",
                "names": {
                    "kind": "StarbugTest",
                    "plural": "tests",
                    "singular": "test",
                    "shortNames": ["test"],
                },
                "group": "bink.com",
                "versions": [
                    {
                        "name": "v1",
                        "served": True,
                        "storage": True,
                        "additionalPrinterColumns": [
                            {
                                "name": "Status",
                                "type": "string",
                                "description": "The status of the test",
                                "jsonPath": ".status.phase",
                            },
                            {
                                "name": "Results",
                                "type": "string",
                                "description": "The results of the test",
                                "jsonPath": ".status.results",
                            },
                            {
                                "name": "Age",
                                "type": "date",
                                "description": "The age of the test",
                                "jsonPath": ".metadata.creationTimestamp",
                            },
                        ],
                        "schema": {
                            "openAPIV3Schema": {
                                "type": "object",
                                "properties": {
                                    "status": {
                                        "type": "object",
                                        "default": {},
                                        "properties": {
                                            "phase": {
                                                "type": "string",
                                                "enum": ["Pending", "Running", "Completed", "Failed"],
                                                "default": "Pending",
                                            },
                                            "results": {"type": "string", "default": ""},
                                        },
                                    },
                                    "spec": {
                                        "type": "object",
                                        "properties": {
                                            "infrastructure": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {"type": "string"},
                                                        "image": {"type": "string"},
                                                    },
                                                },
                                            },
                                            "applications": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {"type": "string"},
                                                        "image": {"type": "string"},
                                                    },
                                                },
                                            },
                                            "test": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "image": {"type": "string"},
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                ],
            },
        },
    )
