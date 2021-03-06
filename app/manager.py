import time
import logging

import httpx

import parser
import utils

from typing import Generator, Iterable, List, Dict, Optional

from feedparser import FeedParserDict

from feeds import Feed, REGISTRY, FEEDS
from storage import feed_entries_db
from web import render_base_page, render_tab_sub_page
from storage.entities import FeedEntry
from feed_classifier.classifier import classify, update_stats, reverse_stats


async def process_feed(feed: Feed) -> None:
    parsed_feed_entries = await parser.parse(feed)

    if not parsed_feed_entries:
        logging.warning('Feed %s is empty', feed.title)

        return

    filtered_entries = await filter_feed_entries(parsed_feed_entries)

    entries_to_save = await prepare_feed_entries(
        feed,
        filtered_entries
    )

    await feed_entries_db.save_many(entries_to_save)


async def filter_feed_entries(
        parsed_feed_entries: List[parser.EntryProxy]
        ) -> Generator[parser.EntryProxy, None, None]:
    fresh_urls = tuple(
        entry.url
        for entry in parsed_feed_entries
        if utils.under_date_threshold(entry)
    )

    exist_urls = await feed_entries_db.filter_exist_urls(fresh_urls)

    new_entries = (
        entry
        for entry in parsed_feed_entries
        if entry.url in fresh_urls and entry.url not in exist_urls
    )

    return new_entries


async def prepare_feed_entries(
        feed: Feed,
        new_parsed_entries: Iterable[FeedParserDict]
        ) -> List[FeedEntry]:
    feed_entries = []

    for entry in new_parsed_entries:
        published_timestamp = entry.published_date or time.time()

        published_summary = '' if feed.skip_summary else entry.summary

        valid = await classify(entry.title, feed.language)

        feed_entries.append(
            FeedEntry(
                title=entry.title,
                url=entry.url,
                published_timestamp=published_timestamp,
                feed=feed.title,
                summary=utils.trim_text(published_summary),
                valid=valid,
            )
        )

    return feed_entries


async def clean_feed_entries_db():
    removed = await feed_entries_db.remove_old()

    if removed:
        logging.info('Feed entries DB cleaned. Removed %d entries', removed)


async def get_base_page(feed_type: str) -> str:
    weather = await get_current_weather()

    html_page = await render_base_page(feed_type, weather)

    return html_page


async def get_tab_sub_page(feed_type: str, last_hours: int) -> str:
    label = utils.label_by_feed_type(feed_type)
    feed_to_entries: Dict[Feed, list] = {f: [] for f in FEEDS}

    news_entries = await feed_entries_db.fetch_last_entries(
        feeds=REGISTRY.keys(),
        valid=label,
        hours_delta=last_hours
    )

    for entry in news_entries:
        feed = REGISTRY[entry.feed]
        feed_to_entries[feed].append(entry)

    html_page = await render_tab_sub_page(
        feed_type,
        last_hours,
        feed_to_entries
    )

    return html_page


async def get_current_weather() -> str:
    weather_service_url = (
        'https://wttr.in/Minsk?'
        'format=%l:+%c+%t+(feels+like+%f),+wind+%w,+%p+%P'
    )

    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(weather_service_url)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logging.error('Error while getting weather: %s', exc)

        weather = ''
    else:
        logging.info('Weather data recieved')

        weather = response.text

    return weather


async def update_feed_classifier(feedback) -> Optional[bool]:
    entry_classified = await feed_entries_db.is_classified(feedback.entry_url)

    if entry_classified is None:
        logging.warning('URL doesn\'t exist %s', feedback.entry_url)

        return

    if entry_classified:
        updated_tokens = await reverse_stats(
            document=feedback.entry_title,
            label=feedback.entry_is_valid,
            language=feedback.entry_language
        )

        updated = bool(updated_tokens)
    else:
        updated_tokens, updated_docs = await update_stats(
            document=feedback.entry_title,
            label=feedback.entry_is_valid,
            language=feedback.entry_language
        )

        updated = bool(updated_tokens and updated_docs)

    if updated:
        await feed_entries_db.update_validity(
            url=feedback.entry_url,
            label=feedback.entry_is_valid
        )

    return updated
