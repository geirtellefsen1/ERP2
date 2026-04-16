# ADR 0001: Custom JWT + OAuth Over Auth0

## Status
Accepted

## Context
ClaudERP needs authentication for three app surfaces (web dashboard, client portal, mobile app). The options considered were:
1. **Auth0** — managed identity provider with SAML, SCIM, MFA, social login out of the box
2. **Custom JWT** — self-issued JWTs with bcrypt password hashing, Google/Microsoft OAuth for social login

## Decision
We chose custom JWT + OAuth because:
- **Cost**: Auth0 charges per MAU; at scale (1000+ agencies × multiple users) this becomes significant
- **Control**: refresh-token rotation, revocation, and MFA are implemented exactly as needed
- **Simplicity**: no external dependency for the critical auth path; reduces outage surface area
- **Nordic compliance**: token storage and key management stay within our EU infrastructure

## Trade-offs
- We own the security surface: password hashing, token signing, brute-force protection
- No built-in SAML/SCIM for enterprise SSO (must build if needed)
- No built-in social login directory sync
- Recovery code management is our responsibility

## Consequences
- Refresh-token rotation with Redis revocation (P1-16) handles session security
- TOTP MFA (P1-18) handles second-factor authentication
- Password reset (P1-17) handles credential recovery
- All secrets encrypted via services/secrets.py

## Revisit Triggers
- More than 10 enterprise customers requiring SAML + SCIM
- Security audit recommends delegating to a managed provider
- Team capacity to maintain auth code drops below safe threshold
