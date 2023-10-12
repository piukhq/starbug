"""Test loop, deploys all of Infra + Olympus."""

from random import choice

from loguru import logger

from starbug.logic.azure import AzureOIDC
from starbug.models.kubernetes.infrastructure.imagepullsecret import BinkCore
from starbug.models.kubernetes.infrastructure.namespace import Namespace
from starbug.models.kubernetes.infrastructure.postgres import Postgres
from starbug.models.kubernetes.infrastructure.rabbitmq import RabbitMQ
from starbug.models.kubernetes.infrastructure.redis import Redis
from starbug.models.kubernetes.olympus.angelia import Angelia
from starbug.models.kubernetes.olympus.asteria import Asteria
from starbug.models.kubernetes.olympus.boreas import Boreas
from starbug.models.kubernetes.olympus.eos import Eos
from starbug.models.kubernetes.olympus.europa import Europa
from starbug.models.kubernetes.olympus.hades import Hades
from starbug.models.kubernetes.olympus.harmonia import Harmonia
from starbug.models.kubernetes.olympus.hermes import Hermes
from starbug.models.kubernetes.olympus.metis import Metis
from starbug.models.kubernetes.olympus.midas import Midas
from starbug.models.kubernetes.olympus.pelops import Pelops
from starbug.models.kubernetes.olympus.plutus import Plutus
from starbug.models.kubernetes.olympus.skiron import Skiron
from starbug.models.kubernetes.olympus.zephyrus import Zephyrus


def main() -> None:
    word1 = choice(["walking", "running", "jumping", "skipping", "hopping"])
    word2 = choice(["red", "blue", "green", "yellow", "orange", "purple", "pink"])
    word3 = choice(["cat", "dog", "bird", "fish", "rabbit", "hamster", "mouse"])

    modules = []

    namespace_name = f"{word1}-{word2}-{word3}"
    modules.append(Namespace(name=namespace_name).complete())
    modules.append(BinkCore(namespace=namespace_name).complete())
    modules.append(Postgres(namespace=namespace_name).complete())
    modules.append(RabbitMQ(namespace=namespace_name).complete())
    modules.append(Redis(namespace=namespace_name).complete())
    modules.append(Angelia(namespace=namespace_name).complete())
    modules.append(Asteria(namespace=namespace_name).complete())
    modules.append(Boreas(namespace=namespace_name).complete())
    modules.append(Eos(namespace=namespace_name).complete())
    modules.append(Europa(namespace=namespace_name).complete())
    modules.append(Hades(namespace=namespace_name).complete())
    modules.append(Harmonia(namespace=namespace_name).complete())
    modules.append(Hermes(namespace=namespace_name).complete())
    modules.append(Metis(namespace=namespace_name).complete())
    modules.append(Midas(namespace=namespace_name).complete())
    modules.append(Pelops(namespace=namespace_name).complete())
    modules.append(Plutus(namespace=namespace_name).complete())
    modules.append(Skiron(namespace=namespace_name).complete())
    modules.append(Zephyrus(namespace=namespace_name).complete())

    AzureOIDC().cleanup_federated_credentials()
    AzureOIDC(namespace=namespace_name).setup_federated_credentials()

    for module in modules:
        for component in module:
            logger.info("Deploying: {}, {}", component.name, component.kind)
            # TODO @cpressland: fix httpx.HTTPStatusError 409 Conflict we get back from k8s occasionally.
            component.create()



if __name__ == "__main__":
    main()
