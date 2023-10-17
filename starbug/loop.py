"""Test loop, deploys all of Infra + Olympus.

This is being kept around as a testing tool for the moment, it will be removed later on.
"""

from random import choice

from loguru import logger

from starbug.azure import AzureOIDC
from starbug.kubernetes.infrastructure.imagepullsecret import BinkCore
from starbug.kubernetes.infrastructure.namespace import Namespace
from starbug.kubernetes.infrastructure.postgres import Postgres
from starbug.kubernetes.infrastructure.rabbitmq import RabbitMQ
from starbug.kubernetes.infrastructure.redis import Redis
from starbug.kubernetes.infrastructure.roles import Roles
from starbug.kubernetes.olympus.angelia import Angelia
from starbug.kubernetes.olympus.asteria import Asteria
from starbug.kubernetes.olympus.boreas import Boreas
from starbug.kubernetes.olympus.eos import Eos
from starbug.kubernetes.olympus.europa import Europa
from starbug.kubernetes.olympus.hades import Hades
from starbug.kubernetes.olympus.harmonia import Harmonia
from starbug.kubernetes.olympus.hermes import Hermes
from starbug.kubernetes.olympus.metis import Metis
from starbug.kubernetes.olympus.midas import Midas
from starbug.kubernetes.olympus.pelops import Pelops
from starbug.kubernetes.olympus.plutus import Plutus
from starbug.kubernetes.olympus.skiron import Skiron
from starbug.kubernetes.olympus.zephyrus import Zephyrus


def main() -> None:
    """Test loop, deploys all Infra + Olympus."""
    word1 = choice(["walking", "running", "jumping", "skipping", "hopping"])
    word2 = choice(["red", "blue", "green", "yellow", "orange", "purple", "pink"])
    word3 = choice(["cat", "dog", "bird", "fish", "rabbit", "hamster", "mouse"])

    modules = []

    namespace_name = f"ait-{word1}-{word2}-{word3}"
    logger.info("Deploying to namespace: {}", namespace_name)
    modules.append(Namespace(name=namespace_name).complete())
    modules.append(Roles(namespace=namespace_name).complete())
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
            try:
                logger.info("Deploying: {}, {}", component.name, component.kind)
                component.create()
            except:  # noqa: E722, S112
                continue

    input("Press enter to cleanup.")
    Namespace(name=namespace_name).namespace.delete()


if __name__ == "__main__":
    main()
