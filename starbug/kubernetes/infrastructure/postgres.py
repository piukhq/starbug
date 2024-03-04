"""Define a Postgres Instance."""

from kr8s.objects import ConfigMap, Deployment, Service, ServiceAccount

from starbug.kubernetes import get_secret_value


class Postgres:
    """Define a Postgres Instance."""

    def __init__(self, namespace: str | None = None, image: str | None = None) -> None:
        """Initialize the Postgres class."""
        self.namespace = namespace or "default"
        self.image = image or "docker.io/postgres:15"
        self.name = "postgres"
        self.labels = {"app": "postgres"}
        self.databases = [
            "api_reflector",
            "atlas",
            "bullsquid",
            "eos",
            "europa",
            "hades",
            "harmonia",
            "hermes",
            "kiroshi",
            "midas",
            "snowstorm",
        ]

        self.pg_host = get_secret_value("azure-postgres", "server_host")
        self.pg_user = get_secret_value("azure-postgres", "server_user")
        self.pg_pass = get_secret_value("azure-postgres", "server_pass")

        self.configmap = ConfigMap(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": self.name + "-scripts",
                    "namespace": self.namespace,
                },
                "data": {
                    "pgloader.sh": f"""#!/bin/bash
                        for database in {" ".join(self.databases)}; do
                        PGPASSWORD="{self.pg_pass}" pg_dump \\
                            --clean --create --no-privileges --no-owner \\
                            --host "{self.pg_host}" \\
                            --username "{self.pg_user}" \\
                            --dbname $database | psql -h localhost -U postgres
                        done
                         """,
                },
            },
        )
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                },
            },
        )
        self.service = Service(
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                    "labels": self.labels,
                },
                "spec": {
                    "ports": [{"port": 5432, "targetPort": 5432}],
                    "selector": self.labels,
                },
            },
        )
        self.deployment = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                    "labels": self.labels,
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels,
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels,
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "postgres",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "volumes": [
                                {
                                    "name": "init-script",
                                    "configMap": {
                                        "name": self.name + "-scripts",
                                    },
                                },
                            ],
                            "containers": [
                                {
                                    "name": "postgres",
                                    "image": self.image,
                                    "ports": [{"containerPort": 5432}],
                                    "readinessProbe": {
                                        "exec": {
                                            "command": [
                                                "pg_isready",
                                                "-U",
                                                "postgres",
                                            ],
                                            "initialDelaySeconds": 5,
                                            "periodSeconds": 10,
                                        },
                                    },
                                    "env": [
                                        {
                                            "name": "POSTGRES_HOST_AUTH_METHOD",
                                            "value": "trust",
                                        },
                                        {
                                            "name": "POSTGRES_MULTIPLE_DATABASES",
                                            "value": ",".join(self.databases),
                                        },
                                    ],
                                    "volumeMounts": [
                                        {
                                            "name": "init-script",
                                            "mountPath": "/docker-entrypoint-initdb.d",
                                            "subPath": "pgloader.sh",
                                        },
                                    ],
                                },
                            ],
                        },
                    },
                },
            },
        )

    def deploy(self) -> tuple[ConfigMap, ServiceAccount, Service, Deployment]:
        """Return all deployable objects as a set."""
        return (self.configmap, self.serviceaccount, self.service, self.deployment)
