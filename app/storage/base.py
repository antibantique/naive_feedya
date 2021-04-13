import aiosqlite
from aiosqlite.cursor import Cursor

from typing import Tuple, List, Any
from collections.abc import Iterable
from pathlib import Path


async def execute(db_filepath: Path, command: str) -> Cursor:
    async with aiosqlite.connect(db_filepath) as db:
        result = await db.execute(command)

        await db.commit()

    return result


async def execute_many(
        db_filepath: Path,
        command: str,
        iterable: Iterable
        ) -> Cursor:
    async with aiosqlite.connect(db_filepath) as db:
        result = await db.executemany(command, iterable)

        await db.commit()

    return result


async def fetch_one(db_filepath: Path, command: str) -> Tuple[Any, ...]:
    async with aiosqlite.connect(db_filepath) as db:
        async with db.execute(command) as cursor:
            result = await cursor.fetchone()

    return result


async def fetch_all(db_filepath: Path, command: str) -> List[Tuple[Any, ...]]:
    async with aiosqlite.connect(db_filepath) as db:
        result = await db.execute_fetchall(command)

    return result
