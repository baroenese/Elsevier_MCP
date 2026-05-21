# Security Policy

## Supported Versions

Security fixes are made on the `main` branch and included in the next tagged release.

## Reporting a Vulnerability

Please report security issues privately to the repository maintainer instead of opening a public issue with exploit details.

Do not include real Elsevier API keys, institutional tokens, licensed full text, or private search output in reports. Use redacted examples and describe the affected command or MCP tool.

## Secret Handling

- Never commit `.env` files, API keys, institutional tokens, or cached licensed responses.
- Rotate any Elsevier, Discord, OpenAI, or institutional token that was pushed publicly.
- Keep live API tests opt-in through environment variables.
