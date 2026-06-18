# Security Policy

## Supported Versions

This repository is a local marketing intelligence and workflow automation system. It may interact with local files, SQLite state, macOS automation, and read-only Gmail API workflows depending on how it is configured.

Security updates apply to the current `main` branch only.

| Version / Branch | Supported |
|---|---|
| `main` | :white_check_mark: |
| Archived branches, forks, or local copies | :x: |

## Scope

Security-sensitive issues may include:

- Accidentally committed secrets, API keys, OAuth tokens, credentials, or private URLs
- Example configuration files that could encourage unsafe credential handling
- Workflows that expose private email, file, project, or reporting data
- Local automation behavior that could modify files or applications unexpectedly
- Logs, state files, or generated reports that may contain sensitive information
- Unsafe defaults that could cause destructive actions without clear preview or consent

Out of scope:

- General feature requests
- Product or UX suggestions
- Low-signal automated reports that do not apply to this repository
- Issues requiring access to private systems not included in the repo
- Misconfiguration in a user's local environment outside the documented setup

## Reporting a Vulnerability

Please do not open a public GitHub issue for security-sensitive concerns.

To report a vulnerability or sensitive-content exposure, contact:

**Jared Silverman**  
**Email:** silverman.jared@gmail.com

Please include:

- A short description of the concern
- The affected file, workflow, command, or configuration if known
- Why the issue may create security, privacy, or data-exposure risk
- Any suggested remediation
- Whether the information appears to be publicly accessible

## Response Expectations

Good-faith reports will be reviewed as soon as practical.

If the report is accepted, remediation may include:

- Removing or redacting sensitive content
- Rotating exposed credentials or tokens
- Updating examples, documentation, or defaults
- Adding clearer dry-run, confirmation, or local-safety guidance
- Revising file handling, logging, or state-management behavior

If the report is declined, the reason will be explained when appropriate.

## Disclosure Policy

Please allow time for review and remediation before sharing any security-sensitive concern publicly.

This repository is intended to support responsible local automation and marketing intelligence workflows. Reports that help keep the project safe, accurate, and appropriately scoped are welcome.
