# backend/src/add_media_data.py
"""
Script for manually adding media sources and their ratings to the database.

This module provides a script (`setup_media_sources`) to manually add MediaSource data
(including third-party ratings and source identifiers) to `news_analysis.db` using Pydantic models, with
last_updated timestamps automatically set to the current time in Kyiv time (EET/UTC+2). It ensures cost
efficiency, reliability (e.g., 300s delays for bias calculation, no fabricated data), and scalability. Logs
progress with emojis (e.g., 💾, 🛠️) and errors to `logs/db_maintenance.log`. Relies on Pydantic, SQLite,
and dateutil.

Dependencies:
    - pydantic: For data validation and serialization (version 2+).
    - sqlite3: For database operations.
    - datetime: For timestamp handling.
    - dateutil: For timezone handling.

Usage:
    >>> python -m src.add_media_data
    💾 Media sources and ratings for NBC News added and bias calculated (last updated: 2025-02-26 22:40:00)
"""

from datetime import datetime

import dateutil

from backend.src.media_utils import (
    calculate_media_bias,
    init_media_database,
    save_media_source,
)
from backend.src.models import MediaSource


def setup_media_sources(db_path: str = "news_analysis.db") -> None:
    """
    Manually adds media sources (including third-party ratings and source identifiers) to the database with automatically updated last_updated timestamps.

    Uses Pydantic models for validation and SQLite for storage, ensuring cost efficiency
    and reliability. Automatically sets last_updated to the current time in Kyiv time (EET/UTC+2) for
    basic data updates and logs progress with emojis and handles errors.

    Args:
        db_path (str, optional): Path to the SQLite database file. Defaults to 'news_analysis.db'.

    Returns:
        None: Updates the database with media source data.

    Example:
        >>> setup_media_sources()
        💾 Media sources and ratings for NBC News added and bias calculated (last updated: 2025-02-26 22:40:00)
    """
    # Initialize database
    init_media_database(db_path)

    # NBC News
    nbc = MediaSource(
        name="NBC News",
        source="nbc",
        country="USA",
        flag_emoji="🇺🇸",
        logo_url="https://logo.clearbit.com/nbcnews.com",
        founded_year=1940,
        website="https://www.nbcnews.com",
        description="NBC News is an American television news network, providing national and international news coverage, headquartered in New York City.",
        owner="Comcast Corporation (via NBCUniversal Media, LLC, publicly traded, revenue from advertising)",
        ownership_category="Large Media Groups",
        rationale_for_ownership="Comcast is a major media entity owning NBCUniversal, which includes NBC News, formed through mergers and acquisitions with significant national and international reach.",
        ad_fontes_bias=round(-0.5738, 2),
        ad_fontes_reliability=0.9,
        ad_fontes_rating_url="https://adfontesmedia.com/nbc-nightly-news-with-lester-holt-bias-and-reliability/",
        ad_fontes_date_rated=datetime(2025, 2, 1),
        allsides_bias=round(-4.5, 2),
        allsides_reliability=0.75,
        allsides_rating_url="https://www.allsides.com/news-source/nbc-news-media-bias",
        allsides_date_rated=datetime(2025, 2, 1),
        media_bias_fact_check_bias=round(-1.8, 2),
        media_bias_fact_check_reliability=0.9,
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/nbc-news/",
        media_bias_fact_check_date_rated=datetime(2025, 2, 1),
    )
    save_media_source(nbc, db_path)

    # Calculate and update bias for NBC News
    bias_result = calculate_media_bias("NBC News", db_path)
    if bias_result:
        nbc.calculated_bias = bias_result["calculated_bias"]
        nbc.calculated_bias_score = bias_result["calculated_bias_score"]
        nbc.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for NBC News added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # Fox News
    fox = MediaSource(
        name="Fox News",
        source="fox_news",
        country="USA",
        flag_emoji="🇺🇸",
        logo_url="https://logo.clearbit.com/foxnews.com",
        founded_year=1996,
        website="https://www.foxnews.com",
        description="Fox News is an American cable news channel, known for conservative-leaning coverage, headquartered in New York City.",
        owner="Fox Corporation (controlled by Rupert Murdoch and family)",
        ownership_category="Corporate Entities",
        rationale_for_ownership="Fox Corporation, a distinct corporate entity, owns Fox News with influence from the Murdoch family, distinct from large media groups due to its specific structure.",
        ad_fontes_bias=round(1.3171, 2),
        ad_fontes_reliability=0.7,
        ad_fontes_rating_url="https://adfontesmedia.com/fox-news-bias-and-reliability/",
        ad_fontes_date_rated=datetime(2025, 2, 1),
        allsides_bias=round(4.85, 2),
        allsides_reliability=0.75,
        allsides_rating_url="https://www.allsides.com/news-source/fox-news-media-bias",
        allsides_date_rated=datetime(2025, 2, 1),
        media_bias_fact_check_bias=round(3.35, 2),
        media_bias_fact_check_reliability=0.6,
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/fox-news-bias/",
        media_bias_fact_check_date_rated=datetime(2025, 2, 1),
    )
    save_media_source(fox, db_path)

    # Calculate and update bias for Fox News
    bias_result = calculate_media_bias("Fox News", db_path)
    if bias_result:
        fox.calculated_bias = bias_result["calculated_bias"]
        fox.calculated_bias_score = bias_result["calculated_bias_score"]
        fox.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for Fox News added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # BBC
    bbc = MediaSource(
        name="BBC",
        source="bbc",
        country="United Kingdom",
        flag_emoji="🇬🇧",
        logo_url="https://logo.clearbit.com/bbc.co.uk",
        founded_year=1922,
        website="https://www.bbc.co.uk",
        description="The BBC is a British public service broadcaster, providing impartial news and programming worldwide.",
        owner="British Broadcasting Corporation (publicly funded via UK license fee under Royal Charter)",
        ownership_category="Government",
        rationale_for_ownership="The BBC is primarily government-funded via license fees under a Royal Charter and subject to government oversight, potentially shaping its editorial direction.",
        ad_fontes_bias=round(-0.1583, 2),
        ad_fontes_reliability=0.9,
        ad_fontes_rating_url="https://adfontesmedia.com/bbc-bias-and-reliability/",
        ad_fontes_date_rated=datetime(2025, 2, 1),
        allsides_bias=round(-2.0, 2),
        allsides_reliability=0.75,
        allsides_rating_url="https://www.allsides.com/news-source/bbc-news-media-bias",
        allsides_date_rated=datetime(2025, 2, 1),
        media_bias_fact_check_bias=round(-1.0, 2),
        media_bias_fact_check_reliability=0.9,
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/bbc/",
        media_bias_fact_check_date_rated=datetime(2025, 2, 1),
    )
    save_media_source(bbc, db_path)

    # Calculate and update bias for BBC
    bias_result = calculate_media_bias("BBC", db_path)
    if bias_result:
        bbc.calculated_bias = bias_result["calculated_bias"]
        bbc.calculated_bias_score = bias_result["calculated_bias_score"]
        bbc.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for BBC added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # Deutsche Welle
    dw = MediaSource(
        name="Deutsche Welle",
        source="dw",
        country="Germany",
        flag_emoji="🇩🇪",
        logo_url="https://logo.clearbit.com/dw.com",
        founded_year=1953,
        website="https://www.dw.com",
        description="Deutsche Welle is Germany's international broadcaster, providing news and analysis in 30 languages.",
        owner="German Government",
        ownership_category="Government",
        rationale_for_ownership="German Government funds DW via tax revenue to provide unbiased journalism globally, under public oversight.",
        ad_fontes_bias=None,
        ad_fontes_reliability=None,
        ad_fontes_rating_url=None,
        ad_fontes_date_rated=None,
        allsides_bias=0.0,
        allsides_reliability=0.75,
        allsides_rating_url="https://www.allsides.com/news-source/deutsche-welle-media-bias/",
        allsides_date_rated=datetime(2025, 2, 1),
        media_bias_fact_check_bias=round(-2.5, 2),
        media_bias_fact_check_reliability=0.9,
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/dw-news/",
        media_bias_fact_check_date_rated=datetime(2024, 12, 20),
    )
    save_media_source(dw, db_path)

    # Calculate and update bias for Deutsche Welle
    bias_result = calculate_media_bias("Deutsche Welle", db_path)
    if bias_result:
        dw.calculated_bias = bias_result["calculated_bias"]
        dw.calculated_bias_score = bias_result["calculated_bias_score"]
        dw.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for Deutsche Welle added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # France24
    france24 = MediaSource(
        name="France 24",
        source="france",
        country="France",
        flag_emoji="🇫🇷",
        logo_url="https://logo.clearbit.com/france24.com",
        founded_year=2006,
        website="https://www.france24.com/en/",
        description="France 24 is a 24-hour, non-stop international news and current affairs television channel and website based in Paris and broadcast in French, English, and Arabic.",
        owner="France Médias Monde (French government)",
        ownership_category="Government",
        rationale_for_ownership="France Médias Monde funds France 24 via tax revenue to provide unbiased journalism globally, under public oversight.",
        ad_fontes_bias=None,
        ad_fontes_reliability=None,
        ad_fontes_rating_url=None,
        ad_fontes_date_rated=None,
        allsides_bias=0.0,
        allsides_reliability=0.75,
        allsides_rating_url="https://www.allsides.com/news-source/france24-media-bias/",
        allsides_date_rated=datetime(2025, 2, 1),
        media_bias_fact_check_bias=round(-2.5, 2),
        media_bias_fact_check_reliability=0.9,
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/france24-news/",
        media_bias_fact_check_date_rated=datetime(2024, 12, 20),
    )
    save_media_source(france24, db_path)

    # Calculate and update bias for France24
    bias_result = calculate_media_bias("France 24", db_path)
    if bias_result:
        france24.calculated_bias = bias_result["calculated_bias"]
        france24.calculated_bias_score = bias_result["calculated_bias_score"]
        france24.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for France 24 added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # The New York Times
    nyt = MediaSource(
        name="The New York Times",
        source="new_york_times",
        country="USA",
        flag_emoji="🇺🇸",
        logo_url="https://logo.clearbit.com/nytimes.com", # Using clearbit for consistency
        founded_year=1851,
        website="https://www.nytimes.com",
        description="The New York Times is a daily newspaper based in New York City, known for its national and international news coverage and analysis. Founded in 1851, it has won numerous Pulitzer Prizes.",
        owner="The New York Times Company (publicly traded, Ochs-Sulzberger family control via Class B shares)",
        ownership_category="Large Media Groups", # Categorized similarly to other large, controlled entities
        rationale_for_ownership="Publicly traded company (NYT) with significant control maintained by the Ochs-Sulzberger family through Class B shares since 1896.",
        # Ratings converted to internal scales (-5 to +5 for bias, 0.0 to 1.0 for reliability)
        ad_fontes_bias=round((-8.05 / 42) * 5, 2), # -0.96
        ad_fontes_reliability=round(41.06 / 64, 2), # 0.64
        ad_fontes_rating_url="https://adfontesmedia.com/the-new-york-times-bias-and-reliability/", # Assumed URL
        ad_fontes_date_rated=datetime(2025, 2, 1), # Consistent date
        allsides_bias=round((-1 / 2) * 5, 2), # -2.5 (Mapping Lean Left = -1)
        allsides_reliability=0.9, # Mapping High = 0.9
        allsides_rating_url="https://www.allsides.com/news-source/new-york-times-media-bias", # Assumed URL
        allsides_date_rated=datetime(2025, 2, 1), # Consistent date
        media_bias_fact_check_bias=round((-4.1 / 10) * 5, 2), # -2.05
        media_bias_fact_check_reliability=0.9, # Mapping High = 0.9
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/new-york-times/", # Assumed URL
        media_bias_fact_check_date_rated=datetime(2025, 2, 1), # Consistent date
    )
    save_media_source(nyt, db_path)

    # Calculate and update bias for The New York Times
    bias_result = calculate_media_bias("The New York Times", db_path)
    if bias_result:
        nyt.calculated_bias = bias_result["calculated_bias"]
        nyt.calculated_bias_score = bias_result["calculated_bias_score"]
        nyt.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for The New York Times added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # Financial Times
    ft = MediaSource(
        name="Financial Times",
        source="financial_times", # Lowercase with underscore
        country="United Kingdom",
        flag_emoji="🇬🇧",
        logo_url="https://logo.clearbit.com/ft.com", # Using clearbit
        founded_year=1888,
        website="https://www.ft.com",
        description="Financial Times is an international newspaper based in London that focuses on economics and business issues, in addition to current events.",
        owner="Nikkei, Inc.", # Japanese media company
        ownership_category="Corporate Entities", # Owned by a large corporation
        rationale_for_ownership="Owned by Nikkei Inc., a major Japanese media corporation, since 2015.",
        # Ratings converted to internal scales (-5 to +5 for bias, 0.0 to 1.0 for reliability)
        ad_fontes_bias=round((-3.82 / 42) * 5, 2), # -0.45
        ad_fontes_reliability=round(44.37 / 64, 2), # 0.69
        ad_fontes_rating_url="https://adfontesmedia.com/financial-times-bias-and-reliability/",
        ad_fontes_date_rated=datetime(2025, 2, 1), # Consistent date
        allsides_bias=round((0 / 2) * 5, 2), # 0.0 (Mapping Center = 0)
        allsides_reliability=0.9, # Mapping High = 0.9 (Assumed)
        allsides_rating_url="https://www.allsides.com/news-source/financial-times-media-bias",
        allsides_date_rated=datetime(2025, 2, 1), # Consistent date
        media_bias_fact_check_bias=round((0.4 / 10) * 5, 2), # 0.2
        media_bias_fact_check_reliability=0.9, # Mapping High = 0.9
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/financial-times/",
        media_bias_fact_check_date_rated=datetime(2025, 2, 1), # Consistent date
    )
    save_media_source(ft, db_path)

    # Calculate and update bias for Financial Times
    bias_result = calculate_media_bias("Financial Times", db_path)
    if bias_result:
        ft.calculated_bias = bias_result["calculated_bias"]
        ft.calculated_bias_score = bias_result["calculated_bias_score"]
        ft.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for Financial Times added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # Wall Street Journal (WSJ)
    wsj = MediaSource(
        name="The Wall Street Journal",
        source="wsj",
        country="USA",
        flag_emoji="🇺🇸",
        logo_url="https://logo.clearbit.com/wsj.com", # Using clearbit
        founded_year=1889,
        website="https://www.wsj.com",
        description="International, business-focused daily newspaper based in New York City, owned by Dow Jones & Company.",
        owner="Dow Jones & Company (News Corp)",
        ownership_category="Large Media Groups", # News Corp is a major media conglomerate
        rationale_for_ownership="Owned by Dow Jones & Company, which is a subsidiary of News Corp, a global media conglomerate controlled by the Murdoch family.",
        # Ratings converted to internal scales (-5 to +5 for bias, 0.0 to 1.0 for reliability)
        ad_fontes_bias=round((4.50 / 42) * 5, 2), # 0.54 (Using explicit score)
        ad_fontes_reliability=round(43.26 / 64, 2), # 0.68
        ad_fontes_rating_url="https://adfontesmedia.com/wall-street-journal-bias-and-reliability/",
        ad_fontes_date_rated=datetime(2025, 2, 1), # Consistent date
        allsides_bias=round((0.0 / 2) * 5, 2), # 0.0 (Mapping Center = 0 for News)
        allsides_reliability=0.9, # Mapping High = 0.9 (Assumed)
        allsides_rating_url="https://www.allsides.com/news-source/wall-street-journal-media-bias",
        allsides_date_rated=datetime(2025, 2, 1), # Consistent date
        media_bias_fact_check_bias=round((2.5 / 10) * 5, 2), # 1.25 (Estimating Right-Center = +2.5)
        media_bias_fact_check_reliability=0.9, # Mapping High = 0.9
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/wall-street-journal/",
        media_bias_fact_check_date_rated=datetime(2025, 2, 1), # Consistent date
    )
    save_media_source(wsj, db_path)

    # Calculate and update bias for Wall Street Journal
    bias_result = calculate_media_bias("The Wall Street Journal", db_path)
    if bias_result:
        wsj.calculated_bias = bias_result["calculated_bias"]
        wsj.calculated_bias_score = bias_result["calculated_bias_score"]
        wsj.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for The Wall Street Journal added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # block our collection with 403 Forbidden error
    # The Daily Wire
    # dwire = MediaSource(
    #     name="The Daily Wire",
    #     source="daily_wire", # Lowercase with underscore
    #     country="USA",
    #     flag_emoji="🇺🇸",
    #     logo_url="https://logo.clearbit.com/dailywire.com", # Using clearbit for consistency
    #     founded_year=2015,
    #     website="https://www.dailywire.com",
    #     description="Politically conservative American news and opinion website founded by Ben Shapiro and Jeremy Boreing.",
    #     owner="Bentkey Ventures, LLC",
    #     ownership_category="Corporate Entities", # Private media company
    #     rationale_for_ownership="Owned by Bentkey Ventures, a private media company.",
    #     # Ratings converted to internal scales (-5 to +5 for bias, 0.0 to 1.0 for reliability)
    #     ad_fontes_bias=round((13.17 / 42) * 5, 2), # 1.57
    #     ad_fontes_reliability=round(30.97 / 64, 2), # 0.48
    #     ad_fontes_rating_url="https://adfontesmedia.com/daily-wire-bias-and-reliability/",
    #     ad_fontes_date_rated=datetime(2025, 2, 1), # Consistent date
    #     allsides_bias=round((2.0 / 2) * 5, 2), # 5.0 (Mapping Right = +2)
    #     allsides_reliability=0.6, # Mapping Mixed/Lower = 0.6 (Based on MBFC)
    #     allsides_rating_url="https://www.allsides.com/news-source/daily-wire",
    #     allsides_date_rated=datetime(2025, 2, 1), # Consistent date
    #     media_bias_fact_check_bias=round((7.2 / 10) * 5, 2), # 3.6
    #     media_bias_fact_check_reliability=round(5.9 / 10, 2), # 0.59
    #     media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/the-daily-wire/",
    #     media_bias_fact_check_date_rated=datetime(2025, 2, 1), # Consistent date
    # )
    # save_media_source(dwire, db_path)

    # # Calculate and update bias for The Daily Wire
    # bias_result = calculate_media_bias("The Daily Wire", db_path)
    # if bias_result:
    #     dwire.calculated_bias = bias_result["calculated_bias"]
    #     dwire.calculated_bias_score = bias_result["calculated_bias_score"]
    #     dwire.bias_confidence = bias_result["bias_confidence"]
    # print(
    #     f"💾 Media sources and ratings for The Daily Wire added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    # )


    # The Christian Post
    cpost = MediaSource(
        name="The Christian Post",
        source="christian_post", # Lowercase with underscore
        country="USA",
        flag_emoji="🇺🇸",
        logo_url="https://logo.clearbit.com/christianpost.com", # Using clearbit for consistency
        founded_year=2004,
        website="https://www.christianpost.com",
        description="American nondenominational, Evangelical Christian news website based in Washington, D.C.",
        owner="Samuel Kim", # Per MBFC
        ownership_category="Corporate Entities", # Assuming structured media outlet
        rationale_for_ownership="Privately owned news organization.",
        # Ratings converted to internal scales (-5 to +5 for bias, 0.0 to 1.0 for reliability)
        ad_fontes_bias=round((10.65 / 42) * 5, 2), # 1.27
        ad_fontes_reliability=round(36.16 / 64, 2), # 0.57
        ad_fontes_rating_url="https://adfontesmedia.com/the-christian-post-bias-and-reliability/",
        ad_fontes_date_rated=datetime(2025, 2, 1), # Consistent date
        allsides_bias=round((2.0 / 2) * 5, 2), # 5.0 (Mapping Right = +2)
        allsides_reliability=0.6, # Estimate based on others
        allsides_rating_url="https://www.allsides.com/news-source/christian-post-media-bias",
        allsides_date_rated=datetime(2025, 2, 1), # Consistent date
        media_bias_fact_check_bias=round((7.0 / 10) * 5, 2), # 3.5 (Estimating Right = +7)
        media_bias_fact_check_reliability=round(6.0 / 10, 2), # 0.6 (Estimating Mixed = 6)
        media_bias_fact_check_rating_url="https://mediabiasfactcheck.com/christian-post/",
        media_bias_fact_check_date_rated=datetime(2025, 2, 1), # Consistent date
    )
    save_media_source(cpost, db_path)

    # Calculate and update bias for The Christian Post
    bias_result = calculate_media_bias("The Christian Post", db_path)
    if bias_result:
        cpost.calculated_bias = bias_result["calculated_bias"]
        cpost.calculated_bias_score = bias_result["calculated_bias_score"]
        cpost.bias_confidence = bias_result["bias_confidence"]
    print(
        f"💾 Media sources and ratings for The Christian Post added and bias calculated (last updated: {datetime.now(dateutil.tz.UTC).strftime('%Y-%m-%d %H:%M:%S')})"
    )


if __name__ == "__main__":
    setup_media_sources()
