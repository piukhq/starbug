"""Simply Loop Utility to sanity check progress."""
from starbug.kube.list import List
from starbug.kube.namespace import Namespace
from starbug.kube.utils import JobTimeoutError, await_kube_job, create_kube_object, delete_kube_namespace
from starbug.templates.essential.binkcore import Binkcore
from starbug.templates.essential.bootstrapdb import BootstrapDB
from starbug.templates.essential.postgres import Postgres
from starbug.templates.essential.rabbitmq import RabbitMQ
from starbug.templates.essential.redis import Redis

try:
    namespace = Namespace()
    binkcore = Binkcore(namespace=namespace.metadata.name)
    postgres = Postgres(namespace=namespace.metadata.name)
    rabbitmq = RabbitMQ(namespace=namespace.metadata.name)
    redis = Redis(namespace=namespace.metadata.name)
    bootstrap_db = BootstrapDB(namespace=namespace.metadata.name)
    deployment = List(
        items=[
            namespace,
            *binkcore,
            *postgres,
            *rabbitmq,
            *redis,
            *bootstrap_db,
        ]
    )
    create_kube_object(deployment.model_dump(by_alias=True))
    print(namespace.metadata.name)
    await_kube_job(namespace=namespace.metadata.name, labels=bootstrap_db.job.metadata.labels)
except JobTimeoutError:
    print("Timeout, killing tests")
    delete_kube_namespace(namespace=namespace.metadata.name)
finally:
    input("Press Enter to kill tests...")
    delete_kube_namespace(namespace=namespace.metadata.name)
