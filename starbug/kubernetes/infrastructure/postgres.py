"""Define a Postgres Instance."""

from kr8s.objects import ConfigMap, Deployment, Service, ServiceAccount


class Postgres:
    """Define a Postgres Instance."""

    def __init__(self, namespace: str | None = None, image: str | None = None) -> None:
        """.Initialize the Postgres class."""
        self.namespace = namespace or "default"
        self.image = image or "docker.io/postgres:15"
        self.name = "postgres"
        self.labels = {"app": "postgres"}
        self.databases = [
            "europa",
            "hades",
            "vela",
            "harmonia",
            "hermes",
            "hubble",
            "api_reflector",
            "zagreus",
            "atlas",
            "midas",
            "carina",
            "copybot",
            "cosmos",
            "momus",
            "eos",
            "polaris",
            "bullsquid",
            "pontus",
            "snowstorm",
            "thanatos",
            "prefect",
            "kiroshi",
        ]
        self.configmap = ConfigMap(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": self.name + "-init-script",
                    "namespace": self.namespace,
                },
                "data": {
                    "create-multiple-postgresql-databases.sh": '#!/bin/bash\n\nset -e\nset -u\n\nfunction create_user_and_database() {\n\tlocal database=$1\n\techo "  Creating user and database \'$database\'"\n\tpsql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" \u003c\u003c-EOSQL\n\t    CREATE USER $database;\n\t    CREATE DATABASE $database;\n\t    GRANT ALL PRIVILEGES ON DATABASE $database TO $database;\nEOSQL\n}\n\nif [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then\n\techo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"\n\tfor db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr \',\' \' \'); do\n\t\tcreate_user_and_database $db\n\tdone\n\techo "Multiple databases created"\nfi\n',  # noqa: E501
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
                                        "name": self.name + "-init-script",
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
