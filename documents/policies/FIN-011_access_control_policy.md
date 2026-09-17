# FIN-011: Access Control Policy

**Policy ID:** FIN-011
**Version:** 1.0
**Effective Date:** 2025-01-15
**Owner:** IT Security & Finance

## Scope
Controls access to the TallyFlow financial platform and defines role permissions.

## Roles
- **Viewer**: Read-only access to dashboards and reports
- **Analyst**: View, investigate, approve low-value items
- **Finance Manager**: Approve within configured thresholds, manage escalations
- **Controller**: Higher approval authority, period management
- **Admin**: System configuration, user management

## Rules
1. All users must authenticate with email and password.
2. Sessions expire after 7 hours of inactivity.
3. API credentials must never be exposed in frontend code.
4. Backend enforces all authorization — frontend permissions are for UX only.
5. Privileged tool credentials (Slack, email, ledger) are backend-only.
