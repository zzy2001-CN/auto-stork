# auto-stork

Daily automation for reading Stork email digests from a 163 mailbox, filtering SCI/JCR Q1-Q2 papers related to semi-supervised medical image segmentation, and archiving the results as Markdown.

## GitHub Secrets

Create these repository secrets before enabling the workflow:

- `MAIL_USERNAME`: your 163 email address.
- `MAIL_AUTH_CODE`: your 163 client authorization code, not your web login password.

The default IMAP endpoint is `imap.163.com:993` over SSL.

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:MAIL_USERNAME="your-address@163.com"
$env:MAIL_AUTH_CODE="your-client-auth-code"
.\.venv\Scripts\python -m stork_mailer.cli --dry-run
```

Parse a saved Stork email sample without connecting to IMAP:

```powershell
.\.venv\Scripts\python -m stork_mailer.cli --sample samples\sample_stork_email.html --dry-run
```

Without `--dry-run`, reports are written to `docs/stork/YYYY-MM-DD.md`. If no matching papers are found, no report is written.

## GitHub Actions

The workflow runs every day at `00:00 UTC`, which is `08:00` in Beijing time, and can also be triggered manually from the Actions tab.

When a report file is generated or changed, the workflow commits it back to the repository. If there are no matching papers, it exits successfully without committing.

## Stork Email Samples

For better parsing accuracy, save a desensitized Stork email as `.html`, `.txt`, or `.eml` under `samples/` and test it with `--sample`. Remove private email addresses, unsubscribe tokens, and personal IDs before committing samples.
