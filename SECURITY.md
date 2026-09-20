# Security Policy

## Reporting Security Vulnerabilities

This is a solo-maintained project — there is no security team, only one
person (mullassery@gmail.com / [@Mullassery](https://github.com/Mullassery)
on GitHub). If you discover a security vulnerability, please report it
privately rather than using the public issue tracker, via either:

- [GitHub Security Advisories](https://github.com/Mullassery/PyRoboSimulator/security/advisories/new)
  for this repo (preferred — keeps the report private until a fix ships), or
- Email to mullassery@gmail.com.

`security@pyrobosimulator.ai` / `info@pyrobosimulator.ai`, previously listed
here, are not real, monitored addresses — that domain is not owned or
checked by the maintainer. Removed.

### What to Include

When reporting a security issue, please provide:

- **Title**: Brief description of the vulnerability type
- **Description**: Detailed explanation of the issue
- **Impact**: Severity assessment (critical, high, medium, low)
- **Reproduction**: Step-by-step instructions to reproduce
- **Version**: PyRoboSimulator version(s) affected
- **Environment**: Python version, OS, deployment (Docker/K8s/standalone)
- **Proof of Concept**: Code or screenshot demonstrating the issue (if safe)
- **Suggested Fix**: Optional mitigation or fix approach
- **Timeline**: Your preferred disclosure timeline

### Response Timeline

No SLA is promised — this is one person maintaining the project outside of
other commitments, not a company with a security team. Best effort, no
committed hours/days figures. In practice: expect an acknowledgment within
a few days, not hours; a fix timeline depends entirely on severity and the
maintainer's availability.

## Supported Versions

There is no back-port policy. Only the latest published release on PyPI
(currently 0.11.x) receives fixes. Older versions are not patched — upgrade
to latest if you need a fix. The version table previously here (claiming
"12 months" / "3 months" support windows for versions 0.1.x/0.2.x, which
predate the current 0.11.x line entirely) was aspirational and did not
reflect anything actually being done; removed rather than left stale.

## Security Best Practices

### For Users

**Installation & Updates**
- Install from official PyPI: `pip install pyrobosimulator`
- Pin to specific versions in production
- Subscribe to security advisories
- Update regularly

**Configuration**
- Never commit secrets to version control
- Use environment variables for sensitive data
- Store `JWT_SECRET_KEY` securely
- Rotate database passwords regularly
- Use strong passwords for PostgreSQL/Redis

**Database Security**
- Enable PostgreSQL SSL connections
- Use parameterized queries (SQLAlchemy handles this)
- Restrict database access to authorized IPs
- Enable connection pooling with size limits
- Monitor database logs for anomalies

**API Security**
- Always use HTTPS in production
- Configure CORS properly (don't use `*` for origins)
- Validate all input via Pydantic
- Implement rate limiting
- Use JWT tokens with short expiry (default: 1 hour)
- Rotate JWT secrets periodically

**Deployment**
- Run as non-root user (UID 1000)
- Use read-only filesystems where possible
- Enable network policies in Kubernetes
- Configure pod security policies
- Use private container registries
- Scan images with Trivy before deployment

### For Developers

**Code Security**
- Never hardcode secrets
- Validate and sanitize all inputs
- Use parameterized queries
- Implement proper error handling
- Don't expose internal details in error messages
- Use type hints to catch bugs
- Enable bandit for security scanning

**Dependencies**
- Keep dependencies updated
- Use `safety check` to verify no known vulnerabilities
- Review dependencies before adding
- Use only OSS with permissive licenses
- Monitor security advisories

**Testing**
- Include security test cases
- Test with malformed/oversized inputs
- Test authentication and authorization
- Use `pytest-security` or similar
- Load test to catch resource exhaustion issues

## Security Architecture

### Authentication & Authorization

- **JWT tokens** (HS256) with bcrypt password hashing
- **Configurable expiry** (default: 1 hour)
- **Secure token storage**: Use HttpOnly cookies or secure storage
- **No sensitive data in tokens**: Only user ID and expiry

### Data Protection

- **Passwords**: Bcrypt with 12 rounds (passlib handles this)
- **Secrets**: Environment variables, never in code
- **Database**: All data encrypted at rest (configurable)
- **In transit**: TLS 1.2+ for all communications

### API Security

- **Input validation**: Pydantic models for all requests
- **Rate limiting**: Configurable per endpoint
- **CORS**: Explicit origin configuration (no wildcards in production)
- **CSRF protection**: FastAPI built-in protection
- **SQL injection prevention**: SQLAlchemy parameterized queries
- **XSS prevention**: JSON responses only (no HTML injection)

### Monitoring & Logging

- **Structured logging**: JSON format with sensitive data filtering
- **Audit trails**: Log all authentication attempts
- **Anomaly detection**: Monitor unusual patterns
- **Prometheus metrics**: Track security-relevant metrics
- **Alerting**: Alert on repeated failures, unusual activity

## Dependency Security

### Vulnerability Scanning

We use:
- `safety` — Check for known vulnerabilities
- `bandit` — Security linting for Python code
- `Trivy` — Container image scanning in CI/CD

Run locally:
```bash
pip install safety bandit
safety check
bandit -r src/
```

### OSS Compliance

All 52 dependencies use permissive licenses (MIT/BSD/Apache 2.0).
See [OSS Compliance Audit](backend/docs/OSS_COMPLIANCE.md).

**No proprietary or GPL code in production.**

## Common Security Issues & Mitigations

### Issue: Exposure of Simulation State via API

**Risk**: Unauthorized access to simulation results or configuration

**Mitigation**:
- Authenticate all endpoints
- Validate user has access to requested simulation
- Implement read/write authorization checks
- Filter sensitive data in responses

### Issue: Resource Exhaustion

**Risk**: Denial of service via large simulations or API spam

**Mitigation**:
- Configure rate limiting
- Set maximum agent count per simulation
- Implement timeout for long-running simulations
- Monitor resource usage
- Use request size limits

### Issue: Injection Attacks

**Risk**: SQL injection, command injection via user input

**Mitigation**:
- Use SQLAlchemy ORM (parameterized queries)
- Validate all inputs with Pydantic
- Never construct SQL strings
- Escape output in error messages

### Issue: Timing Attacks on Authentication

**Risk**: User enumeration via response time analysis

**Mitigation**:
- Use constant-time comparison for tokens
- passlib handles this for password verification
- Add artificial delay to failed logins
- Log failed attempts for security monitoring

## Compliance

No compliance certification (SOC 2, HIPAA, PCI DSS, GDPR or otherwise) has
been obtained or audited for this project, and none is claimed. A previous
version of this file listed SOC 2 Type II / GDPR / HIPAA / PCI DSS as things
the project "aims to support" — none of that has been implemented,
verified, or audited; the claim has been removed rather than left as
unverifiable aspiration. If you need a specific compliance posture, you are
responsible for your own audit of this codebase and deployment.

See [OSS Compliance](backend/docs/OSS_COMPLIANCE.md) for dependency license
information only (that document is about OSS license compliance, not
regulatory compliance).

## Known Security Limitations

### By Design

1. **No built-in multi-tenancy**: Each deployment is single-tenant
2. **No fine-grained role-based access**: Simple user/authenticated model
3. **No end-to-end encryption**: Data encrypted at rest/transport only
4. **No hardware security module**: Keys stored in environment

These are acceptable for research/development use. Production enterprise deployments should implement additional controls.

## Security Checklist for Deployment

Before deploying PyRoboSimulator to production:

- [ ] Database passwords set to strong random values
- [ ] PostgreSQL SSL connections enabled
- [ ] Redis authentication enabled
- [ ] JWT_SECRET_KEY set to strong random value (>32 characters)
- [ ] CORS_ORIGINS configured for your domain only
- [ ] DEBUG mode disabled
- [ ] HTTPS/TLS enabled on reverse proxy
- [ ] Network policies restrict traffic
- [ ] Pod security policies enforced
- [ ] Kubernetes network policies configured
- [ ] Container images scanned with Trivy
- [ ] Non-root user configured (UID 1000)
- [ ] Prometheus monitoring enabled
- [ ] Logs shipped to centralized system
- [ ] Alerts configured for errors/anomalies
- [ ] Database backups tested
- [ ] Disaster recovery plan documented
- [ ] Security testing completed
- [ ] Dependencies audited for vulnerabilities
- [ ] CHANGELOG reviewed for security fixes

## Contact

- **Security reports**: [GitHub Security Advisories](https://github.com/Mullassery/PyRoboSimulator/security/advisories/new)
  or mullassery@gmail.com
- **General questions**: [GitHub Discussions](https://github.com/Mullassery/PyRoboSimulator/discussions)
- **GitHub Issues**: Public, non-security bugs only (use issue templates)

---

**Last updated**: 2026-09-20 (OSS standardization pass — removed fabricated
"Security Team"/SLA/version-support/compliance claims that did not reflect
this being a single-maintainer project; see git history for prior wording).
