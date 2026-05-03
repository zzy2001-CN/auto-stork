# Institutional Access

This project only supports compliant institutional-resource integration paths.

## Recommended Order

1. Official APIs with user-provided API keys.
2. Search alert emails that the user already receives.
3. OpenURL resolver links generated from DOI.
4. User-managed BibTeX/RIS/Zotero exports.

## What Is Not Allowed

- No school SSO browser automation.
- No CAPTCHA or IP restriction bypass.
- No stored school login passwords.
- No automated bulk PDF downloads.
- No scraping of pages behind institutional access controls.

## Supported Skeletons

### Web of Science

Use `WOS_API_KEY` and `WOS_API_TYPE=starter` or `expanded`. Access depends on Clarivate and the institution subscription.

### Elsevier

Use `ELSEVIER_API_KEY`; optionally use `ELSEVIER_INST_TOKEN` for institution-scoped Scopus or ScienceDirect access.

### IEEE

Use `IEEE_API_KEY` for IEEE Metadata Search API access.

### Alert Emails

Use alert emails from WoS, Scopus, IEEE, or ScienceDirect. The parser extracts bibliographic metadata from email content and never clicks restricted full-text links.

### OpenURL

Use `OPENURL_BASE_URL` to generate library resolver links from DOI. The resolver only creates a URL and does not access or download content.

