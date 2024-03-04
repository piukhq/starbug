"""Runs tests depending on state changes to the Starbug CRD."""

from time import sleep

import kr8s
import pendulum
from kr8s.objects import Namespace, Role
from loguru import logger

from starbug.azure import AzureOIDC
from starbug.kubernetes.custom.resources import StarbugTest
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
        modules.append(
            tuple(
                Namespace(
                    {
                        "apiVersion": "v1",
                        "kind": "Namespace",
                        "metadata": {
                            "annotations": {
                                "scheduler.alpha.kubernetes.io/defaultTolerations": [
                                    {
                                        "key": "bink.com/workload",
                                        "operator": "Equal",
                                        "value": "txm",
                                        "effect": "NoSchedule",
                                    },
                                    {
                                        "key": "kubernetes.azure.com/scalesetpriority",
                                        "operator": "Equal",
                                        "value": "spot",
                                        "effect": "NoSchedule",
                                    },
                                ],
                                "scheduler.alpha.kubernetes.io/node-selector": "kubernetes.azure.com/scalesetpriority=spot",
                            },
                            "name": namespace_name,
                        },
                    },
                ),
                Role(
                    {
                        "apiVersion": "rbac.authorization.k8s.io/v1",
                        "kind": "Role",
                        "metadata": {
                            "name": "k8s-wait-for",
                            "namespace": namespace_name,
                        },
                        "rules": [
                            {
                                "apiGroups": [""],
                                "resources": ["pods", "services"],
                                "verbs": ["get", "list", "watch"],
                            },
                            {
                                "apiGroups": ["apps"],
                                "resources": ["deployments"],
                                "verbs": ["get", "list", "watch"],
                            },
                            {
                                "apiGroups": ["batch"],
                                "resources": ["jobs"],
                                "verbs": ["get", "list", "watch"],
                            },
                        ],
                    },
                ),
            ),
        )
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
