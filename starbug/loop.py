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
        namespace.model_dump(by_alias=True),
        postgres.serviceaccount.model_dump(by_alias=True),
        postgres.service.model_dump(by_alias=True),
        postgres.deployment.model_dump(by_alias=True),
        rabbitmq.serviceaccount.model_dump(by_alias=True),
        rabbitmq.service.model_dump(by_alias=True),
        rabbitmq.deployment.model_dump(by_alias=True),
        redis.serviceaccount.model_dump(by_alias=True),
        redis.service.model_dump(by_alias=True),
        redis.deployment.model_dump(by_alias=True),
    ],
)
config.load_config()
api_client = client.ApiClient()
utils.create_from_dict(api_client, deployment.model_dump(by_alias=True))
print(namespace.metadata.name)
sleep(60)
core_client = client.CoreV1Api()
core_client.delete_namespace(name=namespace.metadata.name)
