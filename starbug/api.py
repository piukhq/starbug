from fastapi import FastAPI, status

from starbug.helper import SpecTest, create_test
from starbug.kube.namespace import Namespace

api = FastAPI()


@api.post("/test/create", status_code=status.HTTP_201_CREATED)
def test_create(spec: SpecTest) -> dict:
    """Creates a new Test."""
    return create_test(components=spec.components)


@api.get("/test/status/{namespace}", status_code=status.HTTP_202_ACCEPTED)
def test_status(namespace: str) -> dict:
    """Checks the Status of an ongoing test."""
    return {"status": "in_progress"}



# def b_task() -> None:
#     for _ in range(60):
#         with Path.open("/tmp/progress.txt", "w+") as f:
#             now = datetime.now()
#             f.write(str(now))
#         sleep(1)

# @api.post("/jeff", status_code=status.HTTP_201_CREATED)
# def jeff_create(background_tasks: BackgroundTasks) -> str:
#     background_tasks.add_task(b_task)
#     return "OK"


# @api.post("/jobs/create", status_code=status.HTTP_201_CREATED)
# def job_create() -> dict:
#     """Create a Kubernetes Job."""
#     k = Kube()
#     k.create_job()
#     return {"test_id": k.test_id}


# @api.get("/jobs/{job_id}/status", status_code=status.HTTP_200_OK)
# def job_status(test_id: str, response: Response) -> dict:
#     """Check the Status of a Kubernetes Job."""
#     k = Kube(test_id=test_id)
#     check = k.check_job()
#     if check != "Succeeded":
#         response.status_code = status.HTTP_202_ACCEPTED
#     return {"job_status": check}


# @api.get("/jobs/logs", status_code=status.HTTP_200_OK)
# def job_logs(test_id: str) -> dict:
#     """Get the logs for a Kubernetes Job."""
#     k = Kube(test_id=test_id)
#     logs = k.job_logs()
#     return {"logs": logs}


# @api.get("/jobs/metadata", status_code=status.HTTP_200_OK)
# def job_metadata() -> str:
#     return "jeff"
