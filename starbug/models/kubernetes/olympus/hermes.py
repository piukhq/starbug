"""Defines a Hermes Instance."""

from kr8s.objects import Deployment, Job, Service, ServiceAccount


class Hermes:
    """Defines a Hermes Instance."""

    def __init__(self, namespace: str) -> None:
        """Initialize the Hermes class."""
        self.namespace = namespace
        self.name = "hermes"
        self.image = "binkcore.azurecr.io/hermes:prod"
        self.labels = {"app": "hermes"}
        self.env = {
            "HERMES_DATABASE_URL": "postgres://postgres:postgres@postgres:5432/hermes",
            "RABBIT_DSN": "amqp://guest:guest@rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
        })
        self.service = Service({
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels,
            },
            "spec": {
                "ports": [{"port": 80, "targetPort": 9000}],
                "selector": self.labels,
            },
        })
        self.migrator = Job({
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels,
            },
            "spec": {
                "template": {
                    "metadata": {
                        "labels": self.labels,
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "hermes",
                        },
                    },
                    "spec": {
                        "serviceAccountName": self.name,
                        "containers": [
                            {
                                "name": "hermes",
                                "image": self.image,
                                "command": ["linkerd-await", "--shutdown", "--"],
                                "args": [
                                    "bash",
                                    "-c",
                                    "sleep 10; python manage.py migrate; echo Done",
                                ],
                            },
                        ],
                    },
                },
            },
        })
        self.deployment = Deployment({
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
                            "kubectl.kubernetes.io/default-container": "api",
                        },
                    },
                    "spec": {
                        "serviceAccountName": self.name,
                        "containers": [
                            {
                                "name": "api",
                                "env": self.env,
                                "image": self.image,
                                "command": ["/app/entrypoint.sh"],
                                "args": [
                                    "gunicorn",
                                    "--workers=2",
                                    "--error-logfile=-",
                                    "--access-logfile=-",
                                    "--bind=0.0.0.0:9000",
                                    "hermes.wsgi",
                                ],
                            },
                            {
                                "name": "celery",
                                "env": self.env,
                                "image": self.image,
                                "command": ["linkerd-await", "--"],
                                "args": [
                                    "celery",
                                    "-A",
                                    "hermes",
                                    "worker",
                                    "--without-gossip",
                                    "--without-mingle",
                                    "--loglevel=info",
                                    "--pool=prefork",
                                    "--concurrency=2",
                                    "--queues=ubiquity-async-midas,record-history",
                                    "--events",
                                ],
                            },
                            {
                                "name": "beat",
                                "env": self.env,
                                "image": self.image,
                                "command": ["linkerd-await", "--"],
                                "args": [
                                    "celery",
                                    "-A",
                                    "hermes",
                                    "beat",
                                    "--schedule",
                                    "/tmp/beat",  # noqa: S108
                                    "--pidfile",
                                    "/tmp/beat.pid",  # noqa: S108
                                ],
                            },
                            {
                                "name": "logic",
                                "env": self.env,
                                "image": self.image,
                                "command": ["linkerd-await", "--"],
                                "args": [
                                    "python",
                                    "api_messaging/run.py",
                                ],
                            },
                        ],
                    },
                },
            },
        })
