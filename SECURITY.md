# Security

Poyto handles authentication material and can perform account-changing actions, so credentials must be treated as secrets.

## Never commit

- POYP access or refresh tokens
- Apple identity/access tokens or nonces
- cookies
- raw private traffic exports
- `.env` files
- stable device/vendor identifiers copied from real sessions

The repository `.gitignore` blocks common secret-bearing files, but review every commit before pushing.

## Reporting a security issue

Please avoid filing public issues that contain working credentials, private traffic exports, private account data, or reproducible secrets. Revoke or rotate any credential that may have been exposed.

## Scope

This is an unofficial client. It does not attempt to bypass POYP authorization controls; requests are made using credentials supplied by the authorized account user.
