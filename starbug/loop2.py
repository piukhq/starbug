
import random
import string

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from starbug.models.database import Jobs, engine


def create_job() -> str:
    """Create a job and return its ID."""
    with Session(engine) as session:
        for _ in range(10):
            try:
                job_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=2))  # noqa: S311
                insert = Jobs(
                    id=job_id,
                    components={"test_suite": "starbug:latest", "applications": ["hermes:latest", "midas:latest"]},
                )
                session.add(insert)
                session.commit()
                break
            except IntegrityError:  # noqa: PERF203
                logger.info(f"Duplicate Job ID {job_id}, trying again")
                session.rollback()
                continue
        logger.info(f"Creating job {job_id}")
        return job_id

if __name__ == "__main__":
    for _ in range(10):
        create_job()
