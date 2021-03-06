import datetime

import settings
import utils

from typing import List, Dict

from jinja2 import Environment, FileSystemLoader

from feeds import Feed
from storage.entities import FeedEntry

ENVIRONMENT = Environment(
    loader=FileSystemLoader(settings.TEMPLATES_PATH),
    autoescape=True,
    enable_async=True
)
ENVIRONMENT.filters['format_datetime'] = utils.format_datetime
ENVIRONMENT.filters['reverse_empty_feeds'] = utils.reverse_empty_feeds


async def render_base_page(
        entry_type: str,
        weather: str
        ) -> str:
    tamplate = ENVIRONMENT.get_template(settings.BASE_TEMPLATE_FILENAME)

    title_bg_color, title_font_color = utils.color_pairs_randomizer()

    html_page = await tamplate.render_async(
        title_bg_color=title_bg_color,
        title_font_color=title_font_color,
        feed_datetime=datetime.datetime.now(),
        entry_type=entry_type,
        weather=weather
    )

    return html_page


async def render_tab_sub_page(
        entry_type: str,
        last_hours: int,
        feeds: Dict[Feed, List[FeedEntry]]
        ) -> str:
    tamplate = ENVIRONMENT.get_template(settings.TAB_TEMPLATE_FILENAME)

    html_page = await tamplate.render_async(
        entry_type=entry_type,
        last_hours=last_hours,
        feeds=feeds
    )

    return html_page
