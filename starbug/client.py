from time import sleep

import requests


class Client:
    def __init__(self) -> None:
        pass

    def run_job(self) -> None:
        test = requests.post("http://localhost:6502/run")
        test_id = test.json()["test_id"]
        print(f"Job Created with ID: {test_id}")
        while True:
            sleep(10)
            status = requests.get(
                "http://localhost:6502/status",
                params={"test_id": test_id},
            )
            print(f"Pod State: {status.json()['job_status']}")
            if status.status_code == 200:
                break
        logs = requests.get(
            "http://localhost:6502/logs",
            params={"test_id": test_id},
        )
        print(f"Application Logs: \n{logs.json()['logs']}")
