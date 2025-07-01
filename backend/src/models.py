# backend/src/models.py
"""
Pydantic models for media source data validation and structure.

This module defines a Pydantic model (`MediaSource`) for validating and serializing
media source metadata, third-party ratings, and source identifiers in the news sentiment analysis project.
It ensures data integrity, cost efficiency (e.g., 400 chars/article, leveraging DeepSeek’s caching for ~$0.0128
for 92 articles), and reliability. Uses Pydantic for type hints, validation, and JSON serialization,
assuming Kyiv time (EET/UTC+2) for date handling. Logs errors via `logging` to `logs/db_maintenance.log`.

Dependencies:
    - pydantic: For data validation and serialization (version 2+).
    - typing: For type hints.
    - datetime: For timestamp handling.

Usage:
    >>> from src.models import MediaSource
    >>> nbc = MediaSource(name="NBC News", source="nbc", country="USA", flag_emoji="🇺🇸", logo_url="https://www.nbcnews.com/resources/images/logo-dark.png", website="https://www.nbcnews.com")
"""

import re
from datetime import datetime
from typing import ClassVar, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class MediaSource(BaseModel):
    """
    Represents a media source (e.g., NBC News) with its metadata, calculated bias, third-party ratings, and source identifier.

    Attributes:
        name: The name of the media source (e.g., "NBC News").
        source: The lowercase, underscore-separated source identifier (e.g., "nbc", "fox_news", "bbc"), matching the `name` field in the sources table.
        country: The country of origin (e.g., "USA").
        flag_emoji: Unicode emoji flag for the country (e.g., "🇺🇸").
        logo_url: URL to the media source's logo, hosted on a CDN for efficiency.
        founded_year: Year the source was founded (optional).
        website: Official website URL of the media source.
        description: Brief description of the media source.
        owner: The owning entity or organization (e.g., "Comcast Corporation (via NBCUniversal Media, LLC)") (optional).
        ownership_category: Ownership classification (e.g., "Large Media Groups", "Government", "Corporate Entities") (optional).
        rationale_for_ownership: Rationale or reasoning behind the ownership category assignment (optional).
        calculated_bias: Textual representation of the averaged political bias (e.g., "Center-Left").
        calculated_bias_score: Numeric representation of the averaged political bias on a -5 to +5 scale.
        bias_confidence: Confidence score (0.0–1.0) in the calculated bias, reflecting agreement among ratings.
        last_updated: Timestamp of the last update to basic media source data (automatically set on updates, in Kyiv time).
        ad_fontes_bias: Bias score from Ad Fontes Media (-5 to +5, rounded to 2 decimal places).
        ad_fontes_reliability: Reliability score from Ad Fontes Media (0.0–1.0).
        ad_fontes_rating_url: URL to Ad Fontes Media rating details.
        ad_fontes_date_rated: Date when Ad Fontes Media rated the source.
        allsides_bias: Bias score from AllSides (-5 to +5, rounded to 2 decimal places).
        allsides_reliability: Reliability score from AllSides (0.0–1.0).
        allsides_rating_url: URL to AllSides rating details.
        allsides_date_rated: Date when AllSides rated the source.
        media_bias_fact_check_bias: Bias score from Media Bias/Fact Check (-5 to +5, rounded to 2 decimal places).
        media_bias_fact_check_reliability: Reliability score from Media Bias/Fact Check (0.0–1.0).
        media_bias_fact_check_rating_url: URL to Media Bias/Fact Check rating details.
        media_bias_fact_check_date_rated: Date when Media Bias/Fact Check rated the source.
    """

    name: str = Field(..., max_length=200)
    source: str = Field(
        ...,
        max_length=50,
        description="Lowercase, underscore-separated source identifier (e.g., 'nbc', 'fox_news', 'bbc') matching the name field in the sources table.",
    )
    country: str = Field(..., max_length=100)
    flag_emoji: str = Field(..., max_length=10)
    logo_url: HttpUrl
    founded_year: Optional[int] = None
    website: HttpUrl
    description: Optional[str] = None
    owner: Optional[str] = Field(None, max_length=200)
    ownership_category: Optional[str] = Field(None, max_length=50)
    rationale_for_ownership: Optional[str] = Field(None, max_length=500)
    calculated_bias: Optional[str] = Field(None, max_length=50)
    calculated_bias_score: Optional[float] = Field(None, ge=-5.0, le=5.0)
    bias_confidence: Optional[float] = Field(ge=0.0, le=1.0, default=0.0)
    last_updated: Optional[datetime] = None
    ad_fontes_bias: Optional[float] = None
    ad_fontes_reliability: Optional[float] = Field(None, ge=0.0, le=1.0)
    ad_fontes_rating_url: Optional[HttpUrl] = None
    ad_fontes_date_rated: Optional[datetime] = None
    allsides_bias: Optional[float] = None
    allsides_reliability: Optional[float] = Field(None, ge=0.0, le=1.0)
    allsides_rating_url: Optional[HttpUrl] = None
    allsides_date_rated: Optional[datetime] = None
    media_bias_fact_check_bias: Optional[float] = None
    media_bias_fact_check_reliability: Optional[float] = Field(None, ge=0.0, le=1.0)
    media_bias_fact_check_rating_url: Optional[HttpUrl] = None
    media_bias_fact_check_date_rated: Optional[datetime] = None

    @field_validator("flag_emoji")
    def validate_flag_emoji(cls, value: str) -> str:
        """Validate that the flag_emoji is a valid Unicode emoji."""
        if (
            not value
            or len(value) > 10
            or not all(ord(c) >= 127462 and ord(c) <= 127487 for c in value)
        ):
            raise ValueError("Invalid flag emoji format")
        return value

    @field_validator("ownership_category")
    def validate_ownership_category(cls, value: str) -> str:
        """Validate that the ownership_category is one of the allowed values."""
        if value:
            valid_categories = {
                "Large Media Groups",
                "Private Investment Firms",
                "Individual Ownership",
                "Government",
                "Corporate Entities",
                "Independently Operated",
                "Unclassified",
                "Unverified",
            }
            if value not in valid_categories:
                raise ValueError(
                    f"Ownership category must be one of {valid_categories}"
                )
        return value

    @field_validator("source")
    def validate_source(cls, value: str) -> str:
        """Validate that the source field is lowercase with underscores only."""
        if not value or not isinstance(value, str) or not re.match(r"^[a-z_]+$", value):
            raise ValueError(
                "Source must be a lowercase string with underscores only (e.g., 'nbc', 'fox_news', 'bbc')"
            )
        return value.lower()

    @field_validator(
        "ad_fontes_bias",
        "allsides_bias",
        "media_bias_fact_check_bias",
        "calculated_bias_score",
    )
    def validate_bias_scores(cls, value: float) -> float:
        """Validate that bias scores are within the range -5 to +5."""
        if value is not None:
            if value < -5 or value > 5:
                raise ValueError("Bias score must be between -5 and 5")
        return value

    model_config: ClassVar[dict] = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "name": "NBC News",
                "source": "nbc",
                "country": "USA",
                "flag_emoji": "🇺🇸",
                "logo_url": "https://www.nbcnews.com/resources/images/logo-dark.png",
                "founded_year": 1940,
                "website": "https://www.nbcnews.com",
                "description": "NBC News is an American television news network...",
                "owner": "Comcast Corporation (via NBCUniversal Media, LLC, publicly traded, revenue from advertising)",
                "ownership_category": "Large Media Groups",
                "rationale_for_ownership": "Comcast is a major media entity owning NBCUniversal, which includes NBC News, formed through mergers and acquisitions with significant national and international reach.",
                "calculated_bias": "Lean Left",
                "calculated_bias_score": -2.57,
                "bias_confidence": 0.85,
                "last_updated": "2025-02-26T22:40:00",
                "ad_fontes_bias": -0.57,
                "ad_fontes_reliability": 0.9,
                "ad_fontes_rating_url": "https://adfontesmedia.com/nbc-news-bias-and-reliability/",
                "ad_fontes_date_rated": "2025-02-01T00:00:00",
                "allsides_bias": -4.50,
                "allsides_reliability": 0.75,
                "allsides_rating_url": "https://www.allsides.com/news-source/nbc-news-media-bias",
                "allsides_date_rated": "2025-02-01T00:00:00",
                "media_bias_fact_check_bias": -1.80,
                "media_bias_fact_check_reliability": 0.9,
                "media_bias_fact_check_rating_url": "https://mediabiasfactcheck.com/nbc-news/",
                "media_bias_fact_check_date_rated": "2025-02-01T00:00:00",
            }
        },
    }
