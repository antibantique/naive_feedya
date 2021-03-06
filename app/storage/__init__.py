import settings


def _setup_dbs():
    import asyncio

    from . import feed_entries_db, stats_db

    async def setup_dbs():
        if not settings.FEED_ENTRIES_DB_FILEPATH.exists():
            await feed_entries_db._setup_db()

            print('Feed entries DB created')

        if not settings.STATS_DB_FILEPATH.exists():
            await stats_db._setup_db()

            print('Stats DB created')

    asyncio.run(setup_dbs())


if not settings.FEED_ENTRIES_DB_FILEPATH.exists() or not settings.STATS_DB_FILEPATH.exists():  # noqa
    _setup_dbs()
