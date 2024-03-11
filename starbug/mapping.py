"""Provides a simple mapping of classes to their names."""

from starbug.kubernetes.devops.kiroshi import Kiroshi
from starbug.kubernetes.infrastructure.postgres import Postgres
from starbug.kubernetes.infrastructure.rabbitmq import RabbitMQ
from starbug.kubernetes.infrastructure.redis import Redis
from starbug.kubernetes.olympus.angelia import Angelia
from starbug.kubernetes.olympus.asteria import Asteria
from starbug.kubernetes.olympus.atlas import Atlas
from starbug.kubernetes.olympus.boreas import Boreas
from starbug.kubernetes.olympus.callbacca import Callbacca
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
from starbug.kubernetes.tests.kiroshi import TestKiroshi
from starbug.kubernetes.tests.pytest import Pytest

infrastructure_mapping = {
    "postgres": Postgres,
    "redis": Redis,
    "rabbitmq": RabbitMQ,
}

application_mapping = {
    "angelia": Angelia,
    "atlas": Atlas,
    "asteria": Asteria,
    "boreas": Boreas,
    "callbacca": Callbacca,
    "eos": Eos,
    "europa": Europa,
    "hades": Hades,
    "harmonia": Harmonia,
    "hermes": Hermes,
    "kiroshi": Kiroshi,
    "metis": Metis,
    "midas": Midas,
    "pelops": Pelops,
    "plutus": Plutus,
    "skiron": Skiron,
    "zephyrus": Zephyrus,
}

test_mapping = {
    "test_kiroshi": TestKiroshi,
    "test_pytest": Pytest,
}
