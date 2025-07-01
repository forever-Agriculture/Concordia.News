# docs/media_rating_scales.md

# Media Rating Scales for Automation

This document defines the rating scales and mapping rules for third-party media bias and reliability ratings from Ad Fontes Media, All Sides, and Media Bias/Fact Check, used in the news sentiment analysis project for automating `ThirdPartyRating` data in `src/add_media_data.py` and `src/media_utils.py`. It ensures scalability, reliability (e.g., 300s delays for automation), cost efficiency (e.g., 400 chars/article, no fabricated data), and consistency with Pydantic models and SQLite storage, assuming CET/UTC+1 for date handling. Updated as of February 25, 2025.

## Ad Fontes Media
- **Bias Scale**: Ranges from -42 (Far Left) to +42 (Far Right), with 0 representing the Least Biased position.
- **Reliability Scale**: Ranges from 0 to 64, normalized to 0.0–1.0 for the `reliability_score` in `ThirdPartyRating`.
- **Mapping to -5 to +5 for `bias_score`**: `(Score / 42) * 5`
  - Example: A bias score of -21 maps to `(-21 / 42) * 5 = -2.5`.
  - Reliability normalization: `(Reliability Score / 64)` (e.g., 32 maps to `32 / 64 = 0.5`).

## All Sides
- **Bias Scale**: Ranges from -2 (Left) to +2 (Right), with 0 representing the Center position.
- **Reliability**: Categorized as Low (0.3), Medium (0.6), or High (0.9) for the `reliability_score` in `ThirdPartyRating`.
- **Mapping to -5 to +5 for `bias_score`**: `(Score / 2) * 5`
  - Example: A bias score of -1 maps to `(-1 / 2) * 5 = -2.5`.

## Media Bias/Fact Check
- **Bias Scale**: Ranges from -10 (Far Left) to +10 (Far Right), with 0 representing the Least Biased position.
- **Reliability/Factuality**: Categorized as Low (0.3), Mixed (0.6), or High (0.9) for the `reliability_score` in `ThirdPartyRating`.
- **Mapping to -5 to +5 for `bias_score`**: `(Score / 10) * 5`
  - Example: A bias score of -5 maps to `(-5 / 10) * 5 = -2.5`.

## Usage in Project
These scales are implemented in `src/models.py` (Pydantic `ThirdPartyRating`), `src/media_utils.py` (database operations), and `src/add_media_data.py` (manual data entry). They ensure exact, unrounded `bias_score` values (e.g., -0.5738, +1.3171) and `reliability_score` values (e.g., 0.9, 0.75, 0.6) for NBC News, Fox News, and BBC, supporting automation with 300s delays for reliability and cost efficiency (400 chars/article). Dates (e.g., `date_rated`) are handled in CET/UTC+1 for consistency.

## Notes for Automation
- Use these mappings to transform raw scores from APIs or scraping (e.g., Ground News, Ad Fontes, All Sides, Media Bias/Fact Check) into the -5 to +5 `bias_score` range and 0.0–1.0 `reliability_score` range for `ThirdPartyRating`.
- Schedule updates daily at CET/UTC+1, respecting 300s inter-source and chunk delays to ensure reliability and prevent rate limiting.
- Store raw scores (if available) in `rationale_for_ownership` or a separate table for transparency, maintaining no fabricated data.