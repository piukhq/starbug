"""Runs tests depending on state changes to the Starbug CRD."""

from time import sleep

import kr8s
import pendulum
from httpx import HTTPStatusError
from loguru import logger

from starbug.azure import AzureOIDC
from starbug.kubernetes.custom.resources import StarbugTest
from starbug.kubernetes.devops.kiroshi import Kiroshi
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
from starbug.kubernetes.tests.kiroshi import TestKiroshi


class Worker:
    """Main logic for Creating, Managing and Destroying Starbug Tests."""

    def __init__(self) -> None:
        """Initialize the Starbug Worker class."""
        self.infrastructure_mapping = {
            "postgres": Postgres,
            "redis": Redis,
            "rabbitmq": RabbitMQ,
        }
        self.application_mapping = {
            "angelia": Angelia,
            "asteria": Asteria,
            "boreas": Boreas,
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
        self.test_mapping = {
            "kiroshi": TestKiroshi,
        }

    def get_tests(self) -> None:
        """Get Starbug Tests."""
        while True:
            for test in kr8s.get("tests", namespace="starbug"):
                if test.status.phase == "Pending":
                    self.deploy_test(test)
                if test.status.phase in ("Completed", "Failed"):
                    self.destroy_test(test)
                if test.status.phase == "Running":
                    self.check_running_test(test)
            logger.info("Sleeping for 10 seconds")
            sleep(10)

    def deploy_test(self, test: StarbugTest) -> None:
        """Deploy Starbug Tests."""
        modules = []
        namespace_name = test.metadata.name
        AzureOIDC(namespace=namespace_name).setup_federated_credentials()
        modules.append(Namespace(namespace_name).deploy())
        modules.append(Roles(namespace_name).deploy())
        modules.append(BinkCore(namespace_name).deploy())
        for infrastructure in test.spec.infrastructure:
            name, image = infrastructure.get("name"), infrastructure.get("image")
            modules.append(self.infrastructure_mapping[name](namespace=namespace_name, image=image).deploy())
        for application in test.spec.applications:
            name, image = application.get("name"), application.get("image")
            modules.append(self.application_mapping[name](namespace=namespace_name, image=image).deploy())
        test_suite_name = test.spec.test.get("name")
        test_suite_image = test.spec.test.get("image")
        modules.append(self.test_mapping[test_suite_name](namespace=namespace_name, image=test_suite_image).deploy())
        for module in modules:
            for component in module:
                logger.info(f"Deploying {component.kind}/{component.name}")
                component.create()
        test.patch({"status": {"phase": "Running"}})

    def destroy_test(self, test: StarbugTest) -> None:
        """Destroy Starbug Tests."""
        namespace_name = test.metadata.name
        for namespace in kr8s.get("namespaces", namespace_name):
            logger.info(f"Deleting Namespace: {namespace_name}")
            namespace.delete()
            AzureOIDC(namespace=namespace_name).remove_federated_credentials()

    def check_running_test(self, test: StarbugTest) -> None:
        """Ensure no test is allowed to run for more than two hours."""
        namespace_name = test.metadata.name
        for namespace in kr8s.get("namespaces", namespace_name):
            time_now = pendulum.now()
            time_created = pendulum.parse(namespace.metadata.creationTimestamp)
            time_delta = time_now - time_created
            if time_delta.in_minutes() > 120 and namespace.status.phase == "Active":  # noqa: PLR2004
                logger.info(f"Test {namespace_name} has been running for more than two hours, destroying.")
                test.patch({"status": {"phase": "Failed"}})
                self.destroy_test(test)
