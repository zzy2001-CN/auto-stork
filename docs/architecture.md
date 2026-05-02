# Architecture

`auto-stork` is organized around a small agent pipeline:

1. Load `UserProfile` records from `config/profiles.yml`.
2. Fetch `PaperItem` records from enabled connectors.
3. Deduplicate by DOI, source IDs, and normalized/fuzzy title matching.
4. Score papers with `ranker.py`.
5. Generate innovation summaries from title and abstract only.
6. Save state in SQLite.
7. Write Markdown and HTML daily reports.

## Core Modules

- `stork_agent.models`: shared dataclasses.
- `stork_agent.connectors`: source adapters.
- `stork_agent.deduper`: multi-source merge logic.
- `stork_agent.ranker`: rule-based recommendation scores.
- `stork_agent.summarizer`: extractive innovation summaries.
- `stork_agent.storage.sqlite`: local persistence.
- `stork_agent.report`: Markdown and HTML renderers.
- `stork_agent.pipeline`: daily orchestration.
- `stork_agent.cli`: command-line interface.

`stork_mailer` remains as a compatibility layer for older commands and tests.

## Data Flow

Connector outputs are normalized into `PaperItem`. The pipeline avoids source-specific logic after connector fetch, so future sources such as Web of Science, Elsevier, IEEE, and alert emails can be added without changing report generation.

## Local-First Policy

The system stores local state in SQLite and writes static report files. It does not require a hosted service or user accounts.

