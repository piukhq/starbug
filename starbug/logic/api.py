"""Logic for API Endpoints."""

import random
import string

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from starbug.logic.exceptions import RetryLimitExceededError
from starbug.models.api import SpecTest
from starbug.models.database import Tests, engine

import pendulum


def create_test(spec: SpecTest) -> dict:
    """Create a test and return its ID."""
    with Session(engine) as session:
        retry_limit = 3
        while True:
            try:
                if retry_limit == 0:
                    raise RetryLimitExceededError
                retry_limit -= 1
                test_id = spec.test_id if spec.test_id else "".join(random.choices(string.ascii_lowercase + string.digits, k=6)) # noqa: S311
                insert = Tests(
                    id=test_id,
                    spec=spec.model_dump(exclude_unset=True),
                )
                session.add(insert)
                session.commit()
                break
            except IntegrityError:
                logger.info(f"Duplicate Test ID {test_id}, trying again")
                session.rollback()
                continue
        logger.info(f"Creating Test {test_id}")
    return {"test_id": test_id}

def list_test() -> dict:
    """List tests."""
    with Session(engine) as session:
        query = Tests.select().where(Tests.created_at < pendulum.now().subtract(days=1))
        results = session.execute(query)
        return {"tests": [dict(row) for row in results]}
