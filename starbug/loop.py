from kubernetes import client, config, utils

from starbug.kube.list import List
from starbug.kube.namespace import Namespace
from starbug.templates.essential.binkcore import Binkcore
from starbug.templates.essential.bootstrapdb import BootstrapDB
from starbug.templates.essential.postgres import Postgres
from starbug.templates.essential.rabbitmq import RabbitMQ
from starbug.templates.essential.redis import Redis

namespace = Namespace()
binkcore = Binkcore(namespace=namespace.metadata.name)
postgres = Postgres(namespace=namespace.metadata.name)
rabbitmq = RabbitMQ(namespace=namespace.metadata.name)
redis = Redis(namespace=namespace.metadata.name)
bootstrap_db = BootstrapDB(namespace=namespace.metadata.name)
deployment = List(
    items=[
        namespace,
        binkcore.secret,
        postgres.serviceaccount,
        postgres.service,
        postgres.deployment,
        rabbitmq.serviceaccount,
        rabbitmq.service,
        rabbitmq.deployment,
        redis.serviceaccount,
        redis.service,
        redis.deployment,
        bootstrap_db.job,
    ],
)
config.load_config()
api_client = client.ApiClient()
utils.create_from_dict(api_client, deployment.model_dump(by_alias=True))
print(namespace.metadata.name)
input("Press Enter to kill tests...")
core_client = client.CoreV1Api()
core_client.delete_namespace(name=namespace.metadata.name)
