# Security

## Authentication

| Mode | Configuration | Use case |
|---|---|---|
| `AUTH_PROVIDER=none` | Default; `DEV_USER_ID` used | Local development only |
| `AUTH_PROVIDER=oidc` | `OIDC_ISSUER` + `OIDC_AUDIENCE` | Production |

For production, wire a real JWT validator in `app/security/auth.py::_validate_oidc_token`. The seam is deliberately marked with a comment. Microsoft Entra ID is the recommended provider.

## User isolation

- Every DB query filters by `user_id`.
- Documents, sessions and applications carry an `owner_id` and raise `403 Forbidden` before returning data to another user.
- Personal user documents are **never** ingested into the shared government knowledge base.

## PII handling

- Aadhaar numbers, phone numbers, UDID identifiers, and bank-account-like digit strings are redacted from any extracted text before storage, using `app.security.auth.mask_pii`.
- The `has_aadhaar` boolean field is stored but never the full number.
- Audit logs never contain: Aadhaar numbers, OTPs, passwords, bank account numbers, or private document text.
- Full extracted document text is stored per-user only, PII-redacted.

## Never requested

The system never requests:
- OTPs
- Aadhaar OTP
- Passwords
- PINs
- Banking credentials
- Government portal passwords

## Document intelligence

Document assessments are **descriptive only**. Sahayak AI never claims a certificate is genuine or officially verified.

## File uploads

- MIME type checked against `ALLOWED_UPLOAD_MIMETYPES` allowlist.
- File size checked against `MAX_UPLOAD_MB`.
- Files stored under per-user directories (`/data/uploads/{user_id}/`).

## Input validation

All request bodies use Pydantic v2 models with field constraints. Invalid input returns `422 Unprocessable Entity`.

## Security headers

Added by `SecurityHeadersMiddleware`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=()`

## Rate limiting

Not yet implemented at the application layer. Recommended: use Azure API Management or a reverse proxy (nginx, Traefik) in front of the API for rate limiting and DDoS protection.

## Secrets management

All secrets come from environment variables. No secret is hardcoded. In production, use Azure Key Vault secret references in Container Apps.

## Admin routes

Admin routes check the `is_admin` flag on the user DB record. In production, replace with an Entra ID admin role check.
