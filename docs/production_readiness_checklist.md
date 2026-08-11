# Production Readiness Checklist

## Implemented in repository

- [x] normalized OLTP schema with integrity constraints
- [x] UTC-aware timestamps (`TIMESTAMPTZ`)
- [x] source indexes on incremental columns
- [x] deterministic synthetic data generator
- [x] incremental watermarks with overlap
- [x] idempotent target upserts
- [x] advisory-lock concurrency protection
- [x] raw staging/audit trail
- [x] SCD Type 2 customer dimension
- [x] star-schema facts and dimensions
- [x] data-quality gates
- [x] structured pipeline logs
- [x] Airflow scheduling/retries
- [x] analytics marts
- [x] dashboard provisioning as code
- [x] unit tests
- [x] end-to-end CI workflow
- [x] local Docker reproducibility
- [x] production deployment blueprint

## Environment-specific controls required before a real public production launch

- [ ] managed HA databases
- [ ] TLS certificates and private networking
- [ ] secrets manager/workload identity
- [ ] SSO/RBAC for Airflow and Grafana
- [ ] backup/PITR and restore test evidence
- [ ] centralized monitoring/on-call integration
- [ ] container vulnerability scanning/signing
- [ ] schema migration approval workflow
- [ ] capacity/performance test results
- [ ] defined RPO/RTO and data freshness SLOs
- [ ] CDC/soft-delete strategy if hard-delete capture is required
- [ ] privacy/retention controls for real customer PII

This distinction is intentional: the repository is fully reproducible for portfolio demonstration while avoiding false claims that a single Docker Compose topology is sufficient for enterprise production.
