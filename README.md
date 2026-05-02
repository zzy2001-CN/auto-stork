# auto-stork

`auto-stork` is a lightweight, local-first literature recommendation agent. It collects papers from email alerts and public scholarly APIs, deduplicates records across sources, scores recommendations with transparent rules, and writes daily Markdown/HTML digests.

## Features

- Stork email ingestion through 163 IMAP.
- OpenAlex and Semantic Scholar search.
- PubMed E-utilities and arXiv API connectors.
- Crossref metadata connector.
- Connector skeletons for Web of Science, Elsevier, IEEE, alert emails, and OpenURL resolvers.
- Profile-based search configuration.
- DOI/source/title deduplication.
- Rule-based recommendation scoring.
- SQLite local storage to avoid repeated pushes.
- Markdown and HTML daily reports.

## Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Initialize profile config:

```powershell
python -m stork_agent.cli init-config
```

Run a local dry run:

```powershell
python -m stork_agent.cli run-daily --dry-run
```

The legacy command remains supported:

```powershell
python -m stork_mailer.cli --dry-run
```

## Secrets And Environment

Never commit real API keys, email passwords, or email authorization codes.

Use GitHub repository secrets or local environment variables:

- `MAIL_USERNAME`
- `MAIL_AUTH_CODE`
- `SEMANTIC_SCHOLAR_API_KEY`
- `OPENALEX_API_KEY`
- `NCBI_EMAIL`
- `NCBI_API_KEY`
- `OPENURL_BASE_URL`

Copy `.env.example` for local reference only. Keep real `.env` files untracked.

## Commands

```powershell
python -m stork_agent.cli init-config
python -m stork_agent.cli run-daily
python -m stork_agent.cli run-daily --dry-run
python -m stork_agent.cli test-source openalex
python -m stork_agent.cli test-source semantic_scholar
python -m stork_agent.cli test-source pubmed
python -m stork_agent.cli test-source arxiv
```

Reports are written to:

- `docs/stork/YYYY-MM-DD.md`
- `docs/stork/YYYY-MM-DD.html`

SQLite state is written to `data/stork_agent.sqlite3`.

## Configuration

Primary config lives in `config/profiles.yml`. Legacy `config/search.yml` is still accepted and converted into a default profile when `profiles.yml` is absent.

Each profile supports:

- `keywords`
- `exclude_keywords`
- `sources`
- `lookback_days`
- `daily_limit`
- `min_score`
- `focus_authors`
- `focus_venues`
- `strict_api_keys`

## Safety Boundaries

This project does not implement school account browser automation, SSO bypass, CAPTCHA bypass, password storage, or bulk PDF downloads. Institutional resources must be connected through official APIs, user-provided API keys, email alerts, OpenURL resolvers, or user-managed bibliographic exports.

