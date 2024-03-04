"""Runs tests depending on state changes to the Starbug CRD."""

from time import sleep

import kr8s
import pendulum
from kr8s.objects import Namespace
from loguru import logger

from starbug.azure import AzureOIDC
from starbug.kubernetes.custom.resources import StarbugTest
from starbug.kubernetes.infrastructure.namespace import AITNamespace
from starbug.kubernetes.infrastructure.roles import AITRoles
from starbug.mapping import application_mapping, infrastructure_mapping, test_mapping
from starbug.settings import settings


class Worker:
    """Main logic for Creating, Managing and Destroying Starbug Tests."""

    def __init__(self) -> None:
        """Initialize the Starbug Worker class."""

    def get_tests(self) -> None:
        """Get Starbug Tests."""
        while True:
            for test in kr8s.get("tests", namespace="starbug"):
                if not test.status.complete:
                    if test.status.phase == "Pending":
                        self.deploy_test(test)
                    if test.status.phase in ("Completed", "Failed", "Cancelled"):
                        self.destroy_test(test)
                    if test.status.phase == "Running":
                        self.check_running_test(test)
            sleep(60)

    def deploy_test(self, test: StarbugTest) -> None:
        """Deploy Starbug Tests."""
        modules = []
        namespace_name = test.metadata.name
        AzureOIDC(namespace=namespace_name).setup_federated_credentials()
        modules.append(AITNamespace(namespace_name).deploy())
        modules.append(AITRoles(namespace_name).deploy())
        try:
            for infrastructure in test.spec.infrastructure:
                name, image = infrastructure.get("name"), infrastructure.get("image")
                modules.append(infrastructure_mapping[name](namespace=namespace_name, image=image).deploy())
            for application in test.spec.applications:
                name, image = application.get("name"), application.get("image")
                modules.append(application_mapping[name](namespace=namespace_name, image=image).deploy())
            test_suite_name = test.spec.test.get("name")
            test_suite_image = test.spec.test.get("image")
            modules.append(
                test_mapping[test_suite_name](namespace=namespace_name, image=test_suite_image).deploy(),
            )
        except KeyError:
            logger.info("Failed to deploy test, destroying.")
            test.patch({"status": {"phase": "Failed"}})
            return
        for module in modules:
            for component in module:
                logger.info(f"Deploying {component.kind}/{component.name}")
                component.create()
        test.patch({"status": {"phase": "Running"}})

    def destroy_test(self, test: StarbugTest) -> None:
        """Destroy Starbug Tests."""
        namespace_name = test.metadata.name
        Namespace(namespace_name).delete()
        AzureOIDC(namespace_name).remove_federated_credentials()
        test.patch({"status": {"finished": True}})

    def check_running_test(self, test: StarbugTest) -> None:
        """Ensure no test is allowed to run for more than two hours."""
        namespace_name = test.metadata.name
        namespace = Namespace(namespace_name)
        namespace.refresh()
        time_now = pendulum.now()
        time_created = pendulum.parse(namespace.metadata.creationTimestamp)
        time_delta = time_now - time_created
        if time_delta.in_minutes() > settings.maximum_test_duration_in_minutes:
            logger.info(
                f"Test {namespace_name} has been running for more than {settings.maximum_test_duration_in_minutes} "
                "minutes, marking as failed.",
            )
            test.patch({"status": {"phase": "Failed"}})
