# Security Policy

## Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability, please report it responsibly by emailing security@pyrobosimulator.ai instead of using the public issue tracker.

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

We commit to:
- **24 hours**: Acknowledge receipt of security report
- **48 hours**: Initial assessment and confirmation
- **7 days**: Working patch or mitigation guidance
- **30 days**: Security release with fix

## Supported Versions

Security patches are provided for:

| Version | Support Status | End of Life |
|---------|---|---|
| 0.2.x | Active | 12 months |
| 0.1.x | Limited | 3 months |
| < 0.1 | Unsupported | Immediate |

We recommend always using the latest stable version.

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

PyRoboSimulator aims to support compliance requirements:

- **SOC 2 Type II**: Audit logging, access controls, monitoring
- **GDPR**: Data protection, user data deletion, privacy
- **HIPAA**: Optional data encryption, audit trails (for healthcare deployments)
- **PCI DSS**: No payment processing (scope-dependent)

See [OSS Compliance](backend/docs/OSS_COMPLIANCE.md) for license compliance details.

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

- **Security Team**: security@pyrobosimulator.ai
- **Report vulnerability**: security@pyrobosimulator.ai
- **General questions**: info@pyrobosimulator.ai
- **GitHub Issues**: Public bugs only (use issue templates)

---

**Version**: 1.0  
**Last Updated**: 2024-07-29  
**Next Review**: 2025-01-29
