from time import sleep

from kubernetes import client, config, utils

from starbug.kube.list import List
from starbug.kube.namespace import Namespace
from starbug.templates.postgres import Postgres
from starbug.templates.rabbitmq import RabbitMQ
from starbug.templates.redis import Redis

namespace = Namespace()
postgres = Postgres(namespace=namespace.metadata.name)
rabbitmq = RabbitMQ(namespace=namespace.metadata.name)
redis = Redis(namespace=namespace.metadata.name)
deployment = List(
    items=[
        namespace,
        postgres.serviceaccount,
        postgres.service,
        postgres.deployment,
        rabbitmq.serviceaccount,
        rabbitmq.service,
        rabbitmq.deployment,
        redis.serviceaccount,
        redis.service,
        redis.deployment,
    ],
)
config.load_config()
api_client = client.ApiClient()
utils.create_from_dict(api_client, deployment.model_dump(by_alias=True))
print(namespace.metadata.name)
sleep(60)
core_client = client.CoreV1Api()
core_client.delete_namespace(name=namespace.metadata.name)
