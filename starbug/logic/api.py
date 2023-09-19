"""Logic for API Endpoints."""

import random

import randomname
from loguru import logger
from redis import Redis
from rq import Queue
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from starbug.logic.exceptions import RetryLimitExceededError
from starbug.logic.kubernetes import SetupAIT
from starbug.models.api import SpecTest
from starbug.models.database import Tests, engine


def create_test(spec: SpecTest) -> dict:
    """Create a test and return its ID."""
    queue = Queue(connection=Redis())
    with Session(engine) as session:
        retry_limit = 3
        while True:
            try:
                if retry_limit == 0:
                    raise RetryLimitExceededError
                retry_limit -= 1
                adjective = random.choice(["size", "appearance", "age", "speed"])
                noun = random.choice(["apex_predators", "birds", "ghosts"])
                test_id = randomname.generate(f"adj/{adjective}", "adj/colors", f"nouns/{noun}")
                insert = Tests(
                    id=test_id,
                    spec=spec.model_dump(),
                )
                session.add(insert)
                session.commit()
                queue.enqueue(SetupAIT(test_id=test_id).run)
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
        results = session.execute(query).scalars().all()
        return [{"id": row.id, "status": row.status, "report": row.report} for row in results]

def get_test(test_id: str) -> dict:
    """Get a test."""
    with Session(engine) as session:
        query = select(Tests).where(Tests.id == test_id)
        result = session.execute(query).scalars().first()
        if not result:
            return {}
        return {"id": result.id, "status": result.status, "created_at": result.created_at, "updated_at": result.updated_at, "spec": result.spec, "report": result.report}

def delete_test(test_id: str) -> dict:
    """Delete a test."""
    with Session(engine) as session:
        query = select(Tests).where(Tests.id == test_id)
        result = session.execute(query).scalars().first()
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
        result = session.execute(query).scalars().first()
        if not result:
            return {}
        session.delete(result)
        session.commit()
        return {"test_id": test_id, "purged": True}
