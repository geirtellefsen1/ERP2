[DRAFT — legal review pending]

# Security

ClaudERP takes the security of your data seriously. This page outlines our security practices and infrastructure.

## Infrastructure

Our platform is hosted on enterprise-grade cloud infrastructure with:

- Multi-region deployment for high availability
- Automated backups with point-in-time recovery
- Infrastructure-as-code for reproducible, auditable environments
- Regular penetration testing and vulnerability assessments

## Encryption

- **In transit**: All data is encrypted using TLS 1.2 or higher
- **At rest**: All stored data is encrypted using AES-256
- **Database**: Full disk encryption with managed encryption keys

## Access Control

Row-Level Security (RLS) is enforced at the database level, ensuring that:

- Each tenant can only access their own data
- Administrative access is logged and audited
- Multi-factor authentication is required for all staff access
- Principle of least privilege is applied across all systems

## Incident Response

We maintain a documented incident response plan that includes:

- 24-hour initial response time for security incidents
- Notification to affected parties within 72 hours as required by GDPR
- Post-incident review and remediation procedures

## Responsible Disclosure

If you discover a security vulnerability, please report it to:

security@tellefsen.org

We appreciate responsible disclosure and will acknowledge receipt within 48 hours.
