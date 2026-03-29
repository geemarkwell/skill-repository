# HIPAA Compliance Checklist — Full Reference

This is the authoritative checklist used during audits. Each item must be evaluated as:
- ✅ **Pass** — Fully implemented and verified in code
- ❌ **Fail** — Not implemented or implemented incorrectly
- ⚠️ **Partial** — Partially implemented or cannot be fully verified from code alone
- 🔲 **N/A** — Not applicable to this codebase

### Verification Rule: Trace the Write Path

For any item related to encryption, PHI storage, or data handling, you MUST trace the
full live write path (controller → service → repository → model) before judging pass/fail.
**Do NOT fail items based on model definitions, DTO types, schemas, or interfaces alone.**
Encryption and masking are implemented in the service layer — a `String` column or `str`
field tells you nothing about whether ciphertext or plaintext is stored. See the
"Write-Path Tracing" section in SKILL.md for full details and examples.

---

## 1. Encryption (5 items)

- [ ] 1.1 — Data at rest is encrypted using AES-256 (or equivalent) for all storage containing PHI (databases, file systems, backups). *(Verify via service-layer write path, not model/schema types.)*
- [ ] 1.2 — Data in transit is protected with TLS 1.2 or higher on all connections transmitting PHI.
- [ ] 1.3 — Database fields containing PHI are encrypted at the column/field level, not just at the disk level. *(A String/Text column type is NOT evidence of plaintext. Trace the service write path to see if ciphertext is stored.)*
- [ ] 1.4 — Encryption keys are stored securely (e.g., HSM, KMS) and rotated on a defined schedule.
- [ ] 1.5 — End-to-end encryption is used where applicable (e.g., messaging, file transfers). *(Check the service layer for encrypt-before-persist and decrypt-after-read patterns.)*

## 2. Access Controls (6 items)

- [ ] 2.1 — Role-Based Access Control (RBAC) is implemented — each user role has minimum necessary permissions to access PHI.
- [ ] 2.2 — Multi-Factor Authentication (MFA) is required for all users who access PHI.
- [ ] 2.3 — Automatic session timeouts are enforced after a defined period of inactivity.
- [ ] 2.4 — User access is immediately revoked upon role change or termination.
- [ ] 2.5 — Unique user IDs are assigned — no shared or generic accounts are used to access PHI.
- [ ] 2.6 — Password policies enforce strong passwords (length, complexity, expiration).

## 3. Audit Logging (6 items)

- [ ] 3.1 — All access to PHI (read, create, update, delete) is logged with timestamp, user ID, action, and resource.
- [ ] 3.2 — All authentication events (login, logout, failed attempts, MFA challenges) are logged.
- [ ] 3.3 — Audit logs are immutable — they cannot be modified or deleted by application users.
- [ ] 3.4 — Logs are retained for a minimum of 6 years (per HIPAA requirements).
- [ ] 3.5 — Logs are regularly reviewed for anomalies or unauthorized access patterns.
- [ ] 3.6 — Log storage is encrypted and access-restricted.

## 4. PHI Data Handling (6 items)

- [ ] 4.1 — PHI is never stored in plaintext in caches, cookies, local storage, temp files, or session storage. *(Trace the service write path to confirm what is actually persisted. A plain type declaration is not evidence of plaintext storage.)*
- [ ] 4.2 — PHI is never included in URLs, query strings, or browser history.
- [ ] 4.3 — PHI is never logged in application logs, error messages, stack traces, or debugging output.
- [ ] 4.4 — PHI is never committed to source code, config files, or version control repositories.
- [ ] 4.5 — De-identification or tokenization is used wherever full PHI is not required. *(Check services for tokenization/masking logic — it won't appear in models or DTOs.)*
- [ ] 4.6 — PHI data is purged or anonymized when no longer needed for its original purpose.

## 5. API & Network Security (6 items)

- [ ] 5.1 — All API endpoints that transmit or receive PHI require authentication and authorization.
- [ ] 5.2 — PHI is never passed in query parameters — only in request bodies or headers over encrypted channels.
- [ ] 5.3 — API rate limiting and throttling are in place to prevent abuse.
- [ ] 5.4 — CORS policies are configured to allow only trusted origins.
- [ ] 5.5 — Input validation and sanitization are applied to all endpoints to prevent injection attacks.
- [ ] 5.6 — Network segmentation isolates systems that store or process PHI.

## 6. Third-Party & Infrastructure (4 items)

- [ ] 6.1 — A Business Associate Agreement (BAA) is in place with every third-party vendor or service that touches PHI.
- [ ] 6.2 — Third-party libraries and dependencies are regularly scanned for known vulnerabilities.
- [ ] 6.3 — Cloud infrastructure is configured per the provider's HIPAA-eligible service guidelines.
- [ ] 6.4 — No PHI is sent to third-party analytics, logging, or crash-reporting services without a BAA.

## 7. Backup & Disaster Recovery (4 items)

- [ ] 7.1 — Encrypted backups of all PHI data are performed on a regular schedule.
- [ ] 7.2 — Backup restore procedures are tested at least annually.
- [ ] 7.3 — Backups are stored in a separate, secure location (offsite or separate cloud region).
- [ ] 7.4 — A documented disaster recovery plan exists with defined RTO and RPO.

## 8. Breach Detection & Notification (4 items)

- [ ] 8.1 — Automated monitoring is in place to detect unauthorized access to PHI.
- [ ] 8.2 — An incident response plan is documented and assigns clear roles and responsibilities.
- [ ] 8.3 — The system supports breach notification within 60 days of discovery, as required by HIPAA.
- [ ] 8.4 — Affected individuals, HHS, and (if applicable) media notification procedures are defined.

## 9. Development Practices (6 items)

- [ ] 9.1 — All code changes are subject to peer code review with security considerations.
- [ ] 9.2 — Security decisions and architectural choices are documented.
- [ ] 9.3 — Vulnerability scans are conducted regularly (e.g., OWASP ZAP, Snyk, Dependabot).
- [ ] 9.4 — Penetration testing is performed at least annually.
- [ ] 9.5 — A secure development lifecycle (SDLC) is followed with security checkpoints at each phase.
- [ ] 9.6 — Developers receive HIPAA security awareness training at least annually.

## 10. Physical & Administrative Safeguards (4 items)

- [ ] 10.1 — Server and workstation access is restricted to authorized personnel.
- [ ] 10.2 — Mobile devices accessing PHI enforce encryption and remote wipe capabilities.
- [ ] 10.3 — Written HIPAA policies and procedures are maintained and reviewed annually.
- [ ] 10.4 — A designated HIPAA Security Officer is assigned.

---

**Total checklist items: 51**
