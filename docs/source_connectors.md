# Source Connectors

All connectors implement:

- `name`
- `enabled`
- `validate_config()`
- `fetch(profile, since, limit) -> list[PaperItem]`
- `healthcheck()`

## Implemented Connectors

### Stork Email

Reads Stork alert emails through IMAP. Requires:

- `MAIL_USERNAME`
- `MAIL_AUTH_CODE`

### OpenAlex

Uses OpenAlex Works API. `OPENALEX_API_KEY` is optional. If missing, the connector warns and continues unless the profile enables `strict_api_keys`.

### Semantic Scholar

Uses Semantic Scholar Graph API. `SEMANTIC_SCHOLAR_API_KEY` is recommended.

### PubMed

Uses NCBI E-utilities. Optional:

- `NCBI_EMAIL`
- `NCBI_API_KEY`

### arXiv

Uses the public arXiv Atom API.

### Crossref

Uses Crossref Works API for DOI/title metadata enrichment.

## Institutional Skeletons

### Web of Science

Skeleton for Clarivate Starter/Expanded APIs. Configure `WOS_API_KEY` and `WOS_API_TYPE` (`starter` or `expanded`). Access depends on institution subscription. The current connector validates configuration and reports status, but does not issue real document search requests.

### Elsevier

Skeleton for Scopus Search API and ScienceDirect API. Configure `ELSEVIER_API_KEY`; `ELSEVIER_INST_TOKEN` is optional for institution-scoped access. The current connector exposes query builders and health status only.

### IEEE

Skeleton for IEEE Metadata Search API. Configure `IEEE_API_KEY`. The current connector validates configuration and reserves the metadata search endpoint only.

### Alert Email

Recommended institution-friendly path for WoS, Scopus, IEEE, and ScienceDirect alerts. The connector parses user-received alert emails instead of automating login. It extracts title, DOI, URL, venue, and abstract snippets when present.

### OpenURL Resolver

Generates library resolver links from DOI with `OPENURL_BASE_URL`. It does not visit links or download PDFs.

## Prohibited Integrations

Do not implement school SSO scraping, CAPTCHA bypass, IP restriction bypass, stored login passwords, or automated bulk PDF downloads.

