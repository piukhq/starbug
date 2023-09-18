"""Logic for API Endpoints."""

import random
import string

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from starbug.logic.exceptions import RetryLimitExceededError
from starbug.models.api import SpecTest
from starbug.models.database import Tests, engine


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

def list_test() -> list:
    """List all tests."""
    with Session(engine) as session:
        query = select(Tests)
        results = session.execute(query).all()
        return [row[0].to_dict() for row in results]

def get_test(test_id: str) -> dict:
    """Get a test."""
    with Session(engine) as session:
        query = select(Tests).where(Tests.id == test_id)
        result = session.execute(query).first()
        if not result:
            return {}
        return result[0].to_dict()

def delete_test(test_id: str) -> dict:
    """Delete a test."""
    with Session(engine) as session:
        query = select(Tests).where(Tests.id == test_id)
        result = session.execute(query).first()
        if not result:
            return {}
        update = Tests(
            id=test_id,
            status="deleted",
        )
        session.merge(update)
        session.commit()
        return {"test_id": test_id, "deleted": True}

def purge_test(test_id: str) -> dict:
    """Purge a test."""
    with Session(engine) as session:
        query = select(Tests).where(Tests.id == test_id)
        result = session.execute(query).first()
        if not result:
            return {}
        session.delete(result[0])
        session.commit()
        return {"test_id": test_id, "purged": True}
