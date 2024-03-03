"""Module for defining Scutter elements."""

from kr8s.objects import Role, RoleBinding

from starbug.kubernetes import get_secret_value


def scutter_container(filename: str) -> dict:
    """Return a container definition for scutter.

    Disclaimer: this expects a volume called "results" to be mounted at /mnt/results.

    Args:
        filename (str): The filename to upload to blob storage.

    """
    return {
        "name": "scutter",
        "image": "binkcore.azurecr.io/starbug:latest",
        "imagePullPolicy": "Always",
        "args": ["scutter"],
        "env": [
            {
                "name": "STORAGE_ACCOUNT_DSN",
                "value": get_secret_value("azure-storage", "blob_connection_string_primary"),
            },
            {
                "name": "FILE_PATH",
                "value": f"/mnt/results/{filename}",
            },
        ],
        "volumeMounts": [{"name": "results", "mountPath": "/mnt/results"}],
    }


def scutter_role(namespace: str) -> Role:
    """Return a Role definition for scutter."""
    return Role(
        {
            "metadata": {
                "name": "scutter",
                "namespace": namespace,
            },
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": ["pods"],
                    "verbs": ["get", "watch", "list"],
                },
                {
                    "apiGroups": [""],
                    "resources": ["pods/log"],
                    "verbs": ["get", "watch", "list"],
                },
            ],
        },
    )


def scutter_rolebinding(namespace: str, service_account_name: str) -> RoleBinding:
    """Return a RoleBinding definition for scutter."""
    return RoleBinding(
        {
            "metadata": {
                "name": "scutter",
                "namespace": namespace,
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": service_account_name,
                    "namespace": namespace,
                },
            ],
            "roleRef": {
                "kind": "Role",
                "name": "scutter",
                "apiGroup": "rbac.authorization.k8s.io",
            },
        },
    )
