# Phase 1: Auth Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-08
**Phase:** 1-Auth Foundation
**Areas discussed:** Role assignment at signup, Session & "stay logged in", Password reset experience

---

## Role assignment at signup

| Option | Description | Selected |
|--------|-------------|----------|
| Self-select, librarian needs invite code | Signup form lets the user pick student or librarian; choosing librarian requires an invite/access code from env config | ✓ |
| Default everyone to student; librarians promoted manually | Everyone signs up as student; promotion happens out-of-band | |
| Separate signup links/domains per role | Role implied by university email domain or distinct signup URL | |

**User's choice:** Self-select with invite code required for librarian.
**Notes:** Follow-up — code should be a single shared secret in env config (`LIBRARIAN_SIGNUP_CODE`), not per-invite codes generated in-app (avoids building an invite-management UI for v1). On wrong/missing code: reject signup with a clear error rather than silently downgrading to a student account.

---

## Session & "stay logged in"

| Option | Description | Selected |
|--------|-------------|----------|
| Short access token + long-lived refresh | ~15-30 min access token, ~30-day rotated refresh token in httpOnly cookie | ✓ |
| Short access token + session-length refresh | Refresh token cleared on browser close; must re-login each session | |
| Longer-lived single access token, no rotation | Skip refresh dance; single ~7-day token | |

**User's choice:** Short access token + long-lived (~30 day) rotated refresh token, httpOnly cookie.
**Notes:** Follow-ups covered: (1) token storage on frontend — in-memory access token + httpOnly refresh cookie with silent refresh on load (not localStorage, for XSS protection); (2) logout scope — regular logout revokes only the current session's refresh token, other devices stay logged in; (3) password-reset is an explicit exception — completing a reset revokes ALL sessions for that user, since it's the moment someone regains control of a possibly-compromised account.

| Follow-up: Token storage | Description | Selected |
|--------------------------|-------------|----------|
| In-memory + httpOnly refresh cookie | Access token in JS memory, silently refreshed via cookie | ✓ |
| Access token in localStorage | Simpler but readable by injected scripts (XSS exposure) | |

| Follow-up: Logout/reset revocation scope | Description | Selected |
|------------------------------------------|-------------|----------|
| Logout revokes current session only | Other devices remain logged in | ✓ (for logout) |
| Logout/reset revokes all sessions everywhere | Every device logged out on any logout or reset | |
| Password reset revokes all sessions (separate follow-up) | Reset specifically wipes every session, unlike normal logout | ✓ (for reset) |

---

## Password reset experience

| Option | Description | Selected |
|--------|-------------|----------|
| 1 hour, single-use | Standard balance of usability and exposure window | ✓ |
| 24 hours, single-use | More forgiving but bigger exposure window | |
| 15 minutes, single-use | Tightest security, likely to frustrate users | |

**User's choice:** 1-hour, single-use reset links.
**Notes:** Follow-ups covered: (1) unknown-email handling — always show the same generic "if that email is registered..." message to prevent account enumeration; (2) post-reset flow — auto-login and redirect to dashboard rather than sending the user back to a login page.

| Follow-up: Unknown email response | Description | Selected |
|------------------------------------|-------------|----------|
| Same generic message either way | Prevents account enumeration | ✓ |
| Explicit "no account found" | Friendlier for typos but leaks registered emails | |

| Follow-up: Post-reset behavior | Description | Selected |
|--------------------------------|-------------|----------|
| Auto-login and redirect to dashboard | Smoothest experience, pairs with full session wipe | ✓ |
| Show success message, send to login page | Extra confirmation step | |

---

## Claude's Discretion

- Exact numeric values within the agreed ranges (access token ~15-30 min, refresh token ~30 days).
- Whether the refresh-token table stores extra metadata (device/user-agent/last-used) for a future "manage sessions" view.
- Email verification at signup — raised as a possible area but not selected for discussion. Default assumption for v1: no mandatory email verification (simpler onboarding); flag during planning to confirm.

## Deferred Ideas

None — discussion stayed within the Auth Foundation phase boundary. No new capabilities were proposed during discussion.
