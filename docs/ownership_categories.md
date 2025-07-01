# docs/ownership_categories.md

# Ownership Classifications for Media Sources

This document outlines the ownership classifications used in the news sentiment analysis project to evaluate how ownership shapes media bias. These categories are embedded in the `MediaSource` model, supporting scalability, reliability, and cost efficiency (e.g., 400 chars/article, no fabricated data, with 300s delays for automated processes). Updated as of February 26, 2025, at 9:20 PM CET, adhering to CET/UTC+1 time standards.

## Ownership Classifications

### 1. Large Media Groups
- **Definition**: A network of varied media platforms, such as radio, television, and print, managed by a single organization, often established through mergers and acquisitions. These entities typically hold significant influence across national or global scales (e.g., a major entity like Disney).
- **Justification**: Unified control may lead to consistent editorial perspectives or biases due to extensive reach and corporate strategies.
- **Instance**: Comcast, which oversees NBCUniversal, including NBC News.

### 2. Private Investment Firms
- **Definition**: News entities acquired by private investment entities, often via leveraged buyouts of media assets or their parent companies. These groups may consolidate multiple outlets to lower costs and maximize profits, sometimes at the expense of journalistic integrity.
- **Justification**: A focus on financial performance might compromise editorial independence or content quality.
- **Instance**: A theoretical news outlet owned by a private investment firm (e.g., for future expansion).

### 3. Individual Ownership
- **Definition**: News outlets controlled by individuals with considerable wealth, accumulated outside the media industry, who invest in media properties.
- **Justification**: Personal beliefs or economic interests of the owner could influence reporting, introducing potential bias.
- **Instance**: A hypothetical news source owned by a wealthy individual (e.g., for future consideration).

### 4. Government
- **Definition**: News sources primarily supported by government funding, which may operate with autonomy or serve as a channel for official messaging.
- **Justification**: Public funding or oversight might steer content to reflect governmental agendas, impacting neutrality.
- **Instance**: BBC, supported by UK license fees under a Royal Charter.

### 5. Corporate Entities
- **Definition**: News sources owned by companies that are neither large media groups nor private investment firms. The level of corporate influence on content can differ significantly across outlets.
- **Justification**: Commercial objectives or strategic priorities may subtly bias coverage, though the effect varies by organization.
- **Instance**: Fox Corporation, managing Fox News under Rupert Murdoch’s family control.

### 6. Independently Operated
- **Definition**: Media free from notable corporate or governmental control, determined by a threshold where no entity holds more than 5% ownership that could sway editorial decisions.
- **Justification**: Minimal external influence may enhance objectivity, though cross-ownership complexities require thorough validation.
- **Instance**: A theoretical independent news platform (e.g., for future inclusion).

### 7. Unclassified
- **Definition**: Media outlets that don’t fit into the above categories due to unique or unclear ownership structures.
- **Justification**: Provides adaptability to accommodate atypical ownership scenarios, ensuring broad coverage.
- **Instance**: A hypothetical news source with an unconventional ownership model (e.g., for future use).

### 8. Unverified
- **Definition**: Sources where ownership details are absent, ambiguous, or pending further research.
- **Justification**: Serves as a placeholder for incomplete data, supporting robust automation (e.g., with 300s delays) and future updates.
- **Instance**: An emerging or lesser-known news source lacking ownership records.

## Suggested Improvements
- **Enhanced Criteria**: Include specific benchmarks, such as revenue caps for Large Media Groups or funding percentages for Government sources.
- **Subdivisions**: Add subcategories within Corporate Entities or Large Media Groups (e.g., Technology Firms, Entertainment Companies) to reflect diverse ownership nuances.
- **Automated Updates**: Implement periodic data refreshes using custom scraping tools (with 300s delays) to maintain accuracy under CET/UTC+1.
- **Bias Correlation**: Explore integrating `ownership_category` with `calculated_bias` or `bias_confidence` for deeper insights, preserving cost efficiency (400 chars/article).
- **Validation**: Verify examples against current data sources to ensure relevance.

## Application in Project
These classifications are integrated into `src/models.py` (via the Pydantic `MediaSource` model), `src/media_utils.py` (database integration), and `src/add_media_data.py` (manual input). They enable analysis of ownership effects on bias, with `rationale_for_ownership` storing justifications for transparency and future refinement, ensuring cost-effectiveness across the workflow.
