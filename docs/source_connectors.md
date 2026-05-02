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

Skeleton for Clarivate Starter/Expanded APIs. Access depends on institution subscription.

### Elsevier

Skeleton for Scopus Search API and ScienceDirect API. Supports future API key and institution token configuration.

### IEEE

Skeleton for IEEE Metadata Search API.

### Alert Email

Recommended institution-friendly path for WoS, Scopus, IEEE, and ScienceDirect alerts. The connector will parse user-received alert emails instead of automating login.

### OpenURL Resolver

Generates library resolver links from DOI. It does not download PDFs.

## Prohibited Integrations

Do not implement school SSO scraping, CAPTCHA bypass, IP restriction bypass, stored login passwords, or automated bulk PDF downloads.

