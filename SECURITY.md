# Security Policy

This repository uses example credentials only through `.env.example` and does not contain production secrets.

For production deployments:

- use workload identity and an external secret manager
- enforce TLS and private database endpoints
- give the ETL source account read-only permissions
- give Grafana a read-only marts role
- rotate credentials and audit access
- scan/sign container images
- apply SSO/RBAC to orchestration and BI tools
- classify and protect customer PII

Do not commit `.env`, database dumps containing real customer information, API keys, passwords or private certificates.
