# Phase 1: Auth Foundation - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Students and librarians can register, log in, recover access via password reset, and the system enforces role-separated access (student vs. librarian) server-side for every later feature. This is the security/identity foundation every other phase depends on — no catalog browsing, borrowing, or notification work is in scope here.

</domain>

<decisions>
## Implementation Decisions

### Role assignment at signup
- **D-01:** Signup form lets the user self-select "student" or "librarian." Choosing "librarian" requires entering an invite/access code.
- **D-02:** The invite code is a single shared secret stored in environment config (e.g., `LIBRARIAN_SIGNUP_CODE`) — not per-invite codes generated in-app. Existing librarians share it informally with new hires; rotating it is just changing the env var and redeploying.
- **D-03:** If the librarian code is missing or wrong, reject the signup with a clear error ("Invalid librarian code — check with your library administrator, or sign up as a student"). No silent fallback to a student account.

### Session & "stay logged in"
- **D-04:** Short-lived JWT access token (~15-30 min) + long-lived refresh token (~30 days), rotated on use. This builds on the JWT access + refresh approach already locked in CLAUDE.md's Stack Patterns.
- **D-05:** Refresh token is stored as an httpOnly cookie (not readable by JS). Access token lives only in-memory on the frontend (React state/Zustand) and is silently re-acquired via the refresh cookie on page load — this is how "stay logged in across browser refresh" works without exposing tokens to XSS.
- **D-06:** Regular logout revokes only the current session's refresh token (deleted/rotated server-side); other logged-in devices remain active. Requires a refresh-token table to support per-session revocation.
- **D-07:** Completing a password reset is the one exception: it revokes ALL of that user's active refresh tokens/sessions, not just the current one — this is the moment someone regains control of a potentially-compromised account, so every old session (including a possible attacker's) gets logged out.

### Password reset experience
- **D-08:** Reset links are valid for 1 hour and single-use (expire on first use or after 1 hour, whichever comes first).
- **D-09:** The "request reset" response is identical regardless of whether the email is registered — generic "If that email is registered, you'll receive a reset link shortly" message. Prevents account enumeration via the reset form.
- **D-10:** After successfully setting a new password via the reset link, the user is automatically logged in and redirected to their dashboard (no extra "please log in again" step). This pairs naturally with D-07 — the freshly-created session becomes their one valid session.

### Claude's Discretion
- Exact access-token lifetime within the ~15-30 min range, and exact refresh-token lifetime within the ~30-day range — pick sensible concrete values during planning/implementation.
- Whether the refresh-token table tracks additional metadata (device/user-agent, last-used) beyond what's needed for revocation — useful for a future "manage your sessions" view but not required for v1.
- Email verification at signup was raised as a possible gray area but the user did not select it for discussion — treat as Claude's discretion: a reasonable default for v1 is to allow immediate use without mandatory email verification (keeps onboarding simple), but flag this choice during planning so it can be confirmed or revisited.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Tech stack & architecture (locked)
- `CLAUDE.md` §"Stack Patterns by Variant" — locks: single `users` table with `role` enum (not separate tables), JWT access + refresh token strategy, `require_role()` FastAPI dependency for route gating, `pwdlib[argon2]` for password hashing, `pyjwt` for tokens (not `python-jose`)
- `CLAUDE.md` §"Supporting Libraries" — `pwdlib[argon2]` ≥0.2, `pyjwt` ≥2.9, `python-multipart` (OAuth2 password-flow forms), `fastapi-mail` + `jinja2` for reset emails, Mailpit for dev email capture (`localhost:8025`)

### Project requirements & roadmap
- `.planning/REQUIREMENTS.md` §"Authentication" — AUTH-01 (signup), AUTH-02 (login + persistent session), AUTH-03 (password reset via emailed link), AUTH-04 (server-side role separation)
- `.planning/ROADMAP.md` §"Phase 1: Auth Foundation" — phase goal and 4 success criteria (signup w/ role, persistent login, password reset, server-side 403 enforcement)
- `.planning/PROJECT.md` §"Key Decisions" — "Email/password auth, no university SSO" rationale

No external specs/ADRs beyond CLAUDE.md and the planning docs above — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

This is a greenfield phase — no application code exists yet (only `.planning/` docs and `CLAUDE.md`). There are no reusable components, established patterns, or integration points to map. The researcher and planner should treat this as a from-scratch build following CLAUDE.md's locked stack choices (FastAPI + SQLAlchemy 2.0 async + Alembic + PostgreSQL backend; React 19 + Vite + TanStack Query + Zustand + React Router 7 + shadcn/ui frontend; Docker Compose for orchestration).

### Reusable Assets
- None — first phase, nothing exists to reuse yet.

### Established Patterns
- None established in code yet. CLAUDE.md prescribes the patterns to establish (see canonical_refs above) — this phase is where they get set for the first time and become the template for later phases.

### Integration Points
- This phase produces the `users` table, auth endpoints, JWT issuance/refresh, and the `require_role()` dependency that every subsequent phase (Catalog, Borrowing, Loans, Notifications) will depend on for access control. Get the shape of these right — they're foundational.

</code_context>

<specifics>
## Specific Ideas

- Librarian signup is gated by a shared invite code from env config (`LIBRARIAN_SIGNUP_CODE`) — simplest mechanism that still prevents open self-service librarian access.
- "Stay logged in across refresh" = in-memory access token + httpOnly refresh cookie + silent refresh on load, not localStorage.
- Password reset is treated as a security-sensitive moment: generic enumeration-safe messaging, short single-use links, and a full session wipe on completion.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Email verification at signup was raised as a possible discussion area but not selected; captured as Claude's Discretion above rather than deferred to a future phase, since it's a v1 implementation detail of this same phase, not a new capability.)

### Reviewed Todos (not folded)
None — no pending todos matched this phase.

</deferred>

---

*Phase: 1-Auth Foundation*
*Context gathered: 2026-06-08*
